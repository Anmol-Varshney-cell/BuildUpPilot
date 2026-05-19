import { Language, SubmissionMode, Verdict } from "@prisma/client";
import { Router } from "express";
import { z } from "zod";
import { prisma } from "../config/prisma.js";
import { requireAuth } from "../middleware/auth.js";
import { validateBody } from "../middleware/validate.js";
import { executeInJudge, toJudgeCases } from "../services/judgeClient.js";
const router = Router();
const executeSchema = z.object({
    problemSlug: z.string().min(1),
    language: z.nativeEnum(Language),
    sourceCode: z.string().min(1),
    mode: z.enum(["run", "submit"])
});
router.post("/execute-debug", validateBody(executeSchema), async (req, res, next) => {
    try {
        const { problemSlug, language, sourceCode, mode } = req.body;
        const problem = await prisma.problem.findUnique({
            where: { slug: problemSlug },
            include: { testCases: true }
        });
        if (!problem) {
            res.status(404).json({ message: "Problem not found" });
            return;
        }
        const supported = Array.isArray(problem.supportedLanguages) ? problem.supportedLanguages : [];
        if (!supported.includes(language)) {
            res.status(400).json({ message: "Language not supported for this problem" });
            return;
        }
        const selectedCases = mode === "run" ? problem.testCases.filter((t) => !t.isHidden) : problem.testCases;
        if (selectedCases.length === 0) {
            res.status(400).json({ message: "No test cases configured" });
            return;
        }
        const judgeResult = await executeInJudge({
            sourceCode,
            language,
            mode,
            timeLimitMs: problem.timeLimitMs,
            memoryLimitMb: problem.memoryLimitMb,
            testCases: toJudgeCases(selectedCases)
        });
        res.json({ success: true, result: judgeResult });
    }
    catch (error) {
        console.error("Debug submission error:", error);
        res.status(500).json({ success: false, error: error.message });
    }
});
router.post("/execute", requireAuth, validateBody(executeSchema), async (req, res, next) => {
    try {
        const { problemSlug, language, sourceCode, mode } = req.body;
        const problem = await prisma.problem.findUnique({
            where: { slug: problemSlug },
            include: { testCases: true }
        });
        if (!problem) {
            res.status(404).json({ message: "Problem not found" });
            return;
        }
        const supported = Array.isArray(problem.supportedLanguages) ? problem.supportedLanguages : [];
        if (!supported.includes(language)) {
            res.status(400).json({ message: "Language not supported for this problem" });
            return;
        }
        const selectedCases = mode === "run" ? problem.testCases.filter((t) => !t.isHidden) : problem.testCases;
        if (selectedCases.length === 0) {
            res.status(400).json({ message: "No test cases configured" });
            return;
        }
        const judgeResult = await executeInJudge({
            sourceCode,
            language,
            mode,
            timeLimitMs: problem.timeLimitMs,
            memoryLimitMb: problem.memoryLimitMb,
            testCases: toJudgeCases(selectedCases)
        });
        const maskedCaseResults = judgeResult.testCaseResults.map((c) => ({
            ...c,
            expectedOutput: c.isHidden && mode === "submit" ? undefined : c.expectedOutput,
            actualOutput: c.isHidden && mode === "submit" ? "(hidden)" : c.actualOutput
        }));
        const safeDetails = JSON.parse(JSON.stringify({
            compileOutput: judgeResult.compileOutput ?? null,
            testCaseResults: maskedCaseResults
        }));
        const created = await prisma.submission.create({
            data: {
                userId: req.session.userId,
                problemId: problem.id,
                language,
                sourceCode,
                mode: mode === "run" ? SubmissionMode.RUN : SubmissionMode.SUBMIT,
                verdict: judgeResult.verdict,
                executionTimeMs: judgeResult.executionTimeMs,
                details: safeDetails
            }
        });
        if (mode === "submit" && judgeResult.verdict === Verdict.ACCEPTED) {
            const existingSolve = await prisma.userSolvedProblem.findUnique({
                where: {
                    userId_problemId: {
                        userId: req.session.userId,
                        problemId: problem.id
                    }
                }
            });
            await prisma.userSolvedProblem.upsert({
                where: {
                    userId_problemId: {
                        userId: req.session.userId,
                        problemId: problem.id
                    }
                },
                update: {
                    solvedAt: new Date(),
                    bestTimeMs: existingSolve ? Math.min(existingSolve.bestTimeMs, judgeResult.executionTimeMs) : judgeResult.executionTimeMs,
                    language
                },
                create: {
                    userId: req.session.userId,
                    problemId: problem.id,
                    bestTimeMs: judgeResult.executionTimeMs,
                    language
                }
            });
        }
        res.json({
            submissionId: created.id,
            verdict: judgeResult.verdict,
            executionTimeMs: judgeResult.executionTimeMs,
            compileOutput: judgeResult.compileOutput,
            testCaseResults: maskedCaseResults
        });
    }
    catch (error) {
        next(error);
    }
});
router.get("/me", requireAuth, async (req, res, next) => {
    try {
        const verdict = typeof req.query.verdict === "string" ? req.query.verdict : undefined;
        const language = typeof req.query.language === "string" ? req.query.language : undefined;
        const submissions = await prisma.submission.findMany({
            where: {
                userId: req.session.userId,
                ...(verdict ? { verdict: verdict } : {}),
                ...(language ? { language: language } : {})
            },
            include: {
                problem: { select: { id: true, slug: true, title: true, difficulty: true } }
            },
            orderBy: { createdAt: "desc" },
            take: 100
        });
        res.json({ submissions });
    }
    catch (error) {
        next(error);
    }
});
export default router;
