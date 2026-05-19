import { useMutation, useQuery } from "@tanstack/react-query";
import Editor from "@monaco-editor/react";
import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import AppShell from "../components/AppShell";
import { api } from "../api/client";
import { Language, Submission, Verdict } from "../types";

interface ExecuteResult {
  verdict: Verdict;
  executionTimeMs: number;
  compileOutput?: string;
  testCaseResults: {
    id: string;
    passed: boolean;
    verdict: Verdict;
    actualOutput: string;
    expectedOutput?: string;
    executionTimeMs: number;
    error?: string;
    isHidden: boolean;
  }[];
}

export default function ProblemDetailPage() {
  const { slug = "" } = useParams();
  const [language, setLanguage] = useState<Language>("PYTHON");
  const [sourceCode, setSourceCode] = useState("# Write your solution\n");
  const [result, setResult] = useState<ExecuteResult | null>(null);
  const [execError, setExecError] = useState<string | null>(null);

  const problemQuery = useQuery({
    queryKey: ["problem", slug],
    queryFn: async () => {
      const { data } = await api.get(`/problems/${slug}`);
      return data;
    }
  });

  const starterCode = useMemo(() => {
    const p = problemQuery.data?.problem;
    if (!p?.starterCodes) return sourceCode;
    return p.starterCodes[language] ?? sourceCode;
  }, [problemQuery.data?.problem, language, sourceCode]);

  const executeMutation = useMutation({
    mutationFn: async (mode: "run" | "submit") => {
      try {
        const { data } = await api.post("/submissions/execute", {
          problemSlug: slug,
          language,
          sourceCode,
          mode
        });
        return data as ExecuteResult;
      } catch (err: any) {
        const message =
          err?.response?.data?.message ||
          err?.response?.data?.error ||
          "Execution failed. Please try again.";
        throw new Error(message);
      }
    },
    onSuccess: (data) => {
      setExecError(null);
      setResult(data);
    },
    onError: (err: any) => {
      setExecError(err?.message || "Execution failed. Please try again.");
    }
  });

  const p = problemQuery.data?.problem;
  const submissions: Submission[] = problemQuery.data?.submissions ?? [];

  if (problemQuery.isLoading) {
    return <AppShell><div className="page">Loading...</div></AppShell>;
  }

  if (!p) {
    return <AppShell><div className="page">Problem not found.</div></AppShell>;
  }

  return (
    <AppShell>
      <div className="workspace">
        <section className="statement-panel">
          <div className="statement-header">
            <h2>{p.title}</h2>
            <span className={`difficulty ${p.difficulty.toLowerCase()}`}>{p.difficulty}</span>
          </div>
          <div className="tag-row">
            {p.tags.map((t: string) => (
              <span key={t} className="tag-chip">{t}</span>
            ))}
          </div>
          <article className="statement">{p.statement}</article>
          <h4>Input</h4>
          <pre>{p.inputFormat}</pre>
          <h4>Output</h4>
          <pre>{p.outputFormat}</pre>
          <h4>Constraints</h4>
          <pre>{p.constraints}</pre>
          <h4>Sample Input</h4>
          <pre>{p.sampleInput}</pre>
          <h4>Sample Output</h4>
          <pre>{p.sampleOutput}</pre>
          <h4>Explanation</h4>
          <pre>{p.explanation}</pre>
        </section>

        <section className="editor-panel">
          <div className="editor-toolbar">
            <select
              value={language}
              onChange={(e) => {
                const next = e.target.value as Language;
                setLanguage(next);
                if (p.starterCodes?.[next]) setSourceCode(p.starterCodes[next]);
              }}
            >
              {p.supportedLanguages.map((l: Language) => (
                <option key={l} value={l}>{l}</option>
              ))}
            </select>
            <button className="ghost-btn" onClick={() => setSourceCode(starterCode)}>Reset</button>
            <button className="action-btn" onClick={() => executeMutation.mutate("run")} disabled={executeMutation.isPending}>Run</button>
            <button className="action-btn submit" onClick={() => executeMutation.mutate("submit")} disabled={executeMutation.isPending}>Submit</button>
          </div>

          <Editor
            height="45vh"
            language={language === "CPP" ? "cpp" : language === "JAVASCRIPT" ? "javascript" : language === "HTML" ? "html" : language === "CSS" ? "css" : language.toLowerCase()}
            value={sourceCode}
            onChange={(value) => setSourceCode(value ?? "")}
            options={{ minimap: { enabled: false }, fontSize: 14 }}
          />

          <div className="console">
            <h4>Execution Console</h4>
            {executeMutation.isPending && <p>Running...</p>}
            {execError && <p className="error">{execError}</p>}
            {result && (
              <>
                <p><strong>Verdict:</strong> <span className={`status-pill ${result.verdict === "ACCEPTED" ? "solved" : "pending"}`}>{result.verdict}</span></p>
                <p><strong>Execution Time:</strong> {result.executionTimeMs} ms</p>
                {result.compileOutput && <pre>{result.compileOutput}</pre>}
                <div className="case-results">
                  {result.testCaseResults.map((r) => (
                    <div key={r.id} className="case-item">
                      <p><strong>{r.verdict}</strong> | {r.executionTimeMs} ms</p>
                      {r.error && <pre>{r.error}</pre>}
                      <p>Actual: {r.actualOutput || "(empty)"}</p>
                      {r.expectedOutput !== undefined && <p>Expected: {r.expectedOutput}</p>}
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>

          <div className="submissions-box">
            <h4>Your Recent Submissions</h4>
            <table className="table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Mode</th>
                  <th>Language</th>
                  <th>Verdict</th>
                  <th>Exec(ms)</th>
                </tr>
              </thead>
              <tbody>
                {submissions.map((s) => (
                  <tr key={s.id}>
                    <td>{new Date(s.createdAt).toLocaleString()}</td>
                    <td>{s.mode}</td>
                    <td>{s.language}</td>
                    <td>{s.verdict}</td>
                    <td>{s.executionTimeMs}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </AppShell>
  );
}
