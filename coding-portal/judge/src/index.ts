import express from "express";
import helmet from "helmet";
import os from "os";
import path from "path";
import fs from "fs/promises";
import { spawn } from "child_process";
import { randomUUID } from "crypto";
import { z } from "zod";

const app = express();
app.use(helmet());
app.use(express.json({ limit: "2mb" }));

const Language = z.enum(["C", "CPP", "PYTHON", "JAVA"]);
const schema = z.object({
  sourceCode: z.string().min(1),
  language: Language,
  mode: z.enum(["run", "submit"]),
  timeLimitMs: z.number().int().positive(),
  memoryLimitMb: z.number().int().positive(),
  testCases: z.array(
    z.object({
      id: z.string(),
      input: z.string(),
      expectedOutput: z.string(),
      isHidden: z.boolean()
    })
  ).min(1)
});

type Lang = z.infer<typeof Language>;

type RunResult = { code: number | null; stdout: string; stderr: string; timedOut: boolean; spawnError?: string };

function normalizeOutput(text: string): string {
  return text
    .replace(/\r\n/g, "\n")
    .split("\n")
    .map((line) => line.replace(/[ \t]+$/g, ""))
    .join("\n")
    .replace(/\n+$/g, "");
}

function runProcess(command: string, args: string[], cwd: string, stdin = "", timeoutMs = 2000): Promise<RunResult> {
  return new Promise((resolve) => {
    let proc;
    try {
      proc = spawn(command, args, { cwd, stdio: "pipe", shell: false });
    } catch (error: any) {
      resolve({ code: null, stdout: "", stderr: "", timedOut: false, spawnError: error?.message ?? "Spawn failed" });
      return;
    }

    let stdout = "";
    let stderr = "";
    let timedOut = false;

    const timer = setTimeout(() => {
      timedOut = true;
      proc.kill("SIGKILL");
    }, timeoutMs);

    proc.stdout.on("data", (chunk) => {
      stdout += chunk.toString();
    });

    proc.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
    });

    proc.on("error", (err: any) => {
      clearTimeout(timer);
      resolve({ code: null, stdout, stderr, timedOut: false, spawnError: err?.message ?? "Process error" });
    });

    proc.on("close", (code) => {
      clearTimeout(timer);
      resolve({ code, stdout, stderr, timedOut });
    });

    proc.stdin.write(stdin);
    proc.stdin.end();
  });
}

async function commandExists(command: string): Promise<boolean> {
  const checkCmd = process.platform === "win32" ? "where" : "which";
  const out = await runProcess(checkCmd, [command], process.cwd(), "", 2000);
  return out.code === 0;
}

async function writeWorkspace(language: Lang, sourceCode: string): Promise<{ dir: string; fileName: string }> {
  const dir = path.join(os.tmpdir(), `judge-${randomUUID()}`);
  await fs.mkdir(dir, { recursive: true });

  const fileName =
    language === "C"
      ? "main.c"
      : language === "CPP"
      ? "main.cpp"
      : language === "PYTHON"
      ? "main.py"
      : "Main.java";

  await fs.writeFile(path.join(dir, fileName), sourceCode, "utf8");
  return { dir, fileName };
}

async function compileIfNeeded(language: Lang, dir: string, fileName: string) {
  if (language === "PYTHON") return { ok: true, compileOutput: "" };

  const cmd = language === "C" ? "gcc" : language === "CPP" ? "g++" : "javac";
  const exists = await commandExists(cmd);
  if (!exists) {
    return { ok: false, compileOutput: `${cmd} compiler not installed on host.` };
  }

  const args =
    language === "C"
      ? [fileName, "-O2", "-o", "main"]
      : language === "CPP"
      ? [fileName, "-O2", "-std=c++17", "-o", "main"]
      : [fileName];

  const out = await runProcess(cmd, args, dir, "", 10000);
  if (out.spawnError || out.code !== 0) {
    return { ok: false, compileOutput: out.spawnError || out.stderr || out.stdout || "Compilation failed" };
  }

  return { ok: true, compileOutput: "" };
}

async function runCase(language: Lang, dir: string, input: string, timeoutMs: number): Promise<RunResult> {
  if (language === "PYTHON") {
    const exists = await commandExists("python");
    if (!exists) return { code: null, stdout: "", stderr: "", timedOut: false, spawnError: "python runtime not installed" };
    return runProcess("python", ["main.py"], dir, input, timeoutMs);
  }

  if (language === "JAVA") {
    const exists = await commandExists("java");
    if (!exists) return { code: null, stdout: "", stderr: "", timedOut: false, spawnError: "java runtime not installed" };
    return runProcess("java", ["Main"], dir, input, timeoutMs);
  }

  const exe = process.platform === "win32" ? "main.exe" : "./main";
  return runProcess(exe, [], dir, input, timeoutMs);
}

app.post("/execute", async (req, res) => {
  const parsed = schema.safeParse(req.body);
  if (!parsed.success) {
    res.status(400).json({ verdict: "INTERNAL_ERROR", message: "Invalid request", testCaseResults: [] });
    return;
  }

  const payload = parsed.data;
  const { language, sourceCode, testCases, timeLimitMs } = payload;
  let workspace: { dir: string; fileName: string } | null = null;

  try {
    workspace = await writeWorkspace(language, sourceCode);

    const compile = await compileIfNeeded(language, workspace.dir, workspace.fileName);
    if (!compile.ok) {
      res.json({ verdict: "COMPILATION_ERROR", executionTimeMs: 0, compileOutput: compile.compileOutput, testCaseResults: [] });
      return;
    }

    let finalVerdict = "ACCEPTED";
    let maxTime = 0;
    const testCaseResults: any[] = [];

    for (const tc of testCases) {
      const start = Date.now();
      const run = await runCase(language, workspace.dir, tc.input, timeLimitMs);
      const spent = Date.now() - start;
      maxTime = Math.max(maxTime, spent);

      if (run.timedOut) {
        finalVerdict = "TIME_LIMIT_EXCEEDED";
        testCaseResults.push({ id: tc.id, passed: false, verdict: finalVerdict, actualOutput: "", expectedOutput: tc.expectedOutput, executionTimeMs: spent, error: "Time limit exceeded", isHidden: tc.isHidden });
        break;
      }

      if (run.spawnError || (run.code ?? 1) !== 0) {
        finalVerdict = "RUNTIME_ERROR";
        testCaseResults.push({ id: tc.id, passed: false, verdict: finalVerdict, actualOutput: run.stdout, expectedOutput: tc.expectedOutput, executionTimeMs: spent, error: run.spawnError || run.stderr || "Runtime error", isHidden: tc.isHidden });
        break;
      }

      const actualNorm = normalizeOutput(run.stdout);
      const expectedNorm = normalizeOutput(tc.expectedOutput);
      if (actualNorm !== expectedNorm) {
        finalVerdict = "WRONG_ANSWER";
        testCaseResults.push({ id: tc.id, passed: false, verdict: finalVerdict, actualOutput: run.stdout, expectedOutput: tc.expectedOutput, executionTimeMs: spent, isHidden: tc.isHidden });
        break;
      }

      testCaseResults.push({ id: tc.id, passed: true, verdict: "ACCEPTED", actualOutput: run.stdout, expectedOutput: tc.expectedOutput, executionTimeMs: spent, isHidden: tc.isHidden });
    }

    res.json({ verdict: finalVerdict, executionTimeMs: maxTime, compileOutput: "", testCaseResults });
  } catch (error: any) {
    res.status(500).json({ verdict: "INTERNAL_ERROR", executionTimeMs: 0, compileOutput: error?.message || "Internal judge error", testCaseResults: [] });
  } finally {
    if (workspace) await fs.rm(workspace.dir, { recursive: true, force: true });
  }
});

app.get("/health", (_req, res) => {
  res.json({ status: "ok" });
});

const port = Number(process.env.PORT ?? 5001);
app.listen(port, () => {
  console.log(`Judge running on port ${port}`);
});
