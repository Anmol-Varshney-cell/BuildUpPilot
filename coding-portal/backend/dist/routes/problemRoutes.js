import { Difficulty, Language } from "@prisma/client";
import { Router } from "express";
import { z } from "zod";
import { prisma } from "../config/prisma.js";
const router = Router();
const listQuerySchema = z.object({
    difficulty: z.nativeEnum(Difficulty).optional(),
    tag: z.string().optional(),
    language: z.nativeEnum(Language).optional(),
    q: z.string().optional()
});
router.get("/", async (req, res, next) => {
    try {
        const cleanedQuery = {
            difficulty: typeof req.query.difficulty === "string" && req.query.difficulty.trim() ? req.query.difficulty : undefined,
            tag: typeof req.query.tag === "string" && req.query.tag.trim() ? req.query.tag.trim() : undefined,
            language: typeof req.query.language === "string" && req.query.language.trim() ? req.query.language : undefined,
            q: typeof req.query.q === "string" && req.query.q.trim() ? req.query.q.trim() : undefined
        };
        const parsed = listQuerySchema.safeParse(cleanedQuery);
        if (!parsed.success) {
            res.status(400).json({ message: "Invalid filters" });
            return;
        }
        const { difficulty, tag, language, q } = parsed.data;
        const where = {};
        if (difficulty)
            where.difficulty = difficulty;
        if (q)
            where.OR = [{ title: { contains: q } }, { statement: { contains: q } }];
        let problems = await prisma.problem.findMany({
            where,
            orderBy: [{ difficulty: "asc" }, { title: "asc" }],
            select: {
                id: true,
                slug: true,
                title: true,
                difficulty: true,
                tags: true,
                supportedLanguages: true
            }
        });
        if (tag) {
            const lowTag = tag.toLowerCase();
            problems = problems.filter((p) => Array.isArray(p.tags) && p.tags.some((t) => t.toLowerCase().includes(lowTag) || lowTag.includes(t.toLowerCase())));
        }
        if (language) {
            problems = problems.filter((p) => Array.isArray(p.supportedLanguages) && p.supportedLanguages.includes(language));
        }
        // Only show solved status if user is authenticated
        if (req.session.userId) {
            const solved = await prisma.userSolvedProblem.findMany({
                where: { userId: req.session.userId },
                select: { problemId: true }
            });
            const solvedSet = new Set(solved.map((s) => s.problemId));
            res.json({
                problems: problems.map((p) => ({ ...p, solved: solvedSet.has(p.id) }))
            });
        }
        else {
            res.json({
                problems: problems.map((p) => ({ ...p, solved: false }))
            });
        }
    }
    catch (error) {
        next(error);
    }
});
router.get("/:slug", async (req, res, next) => {
    try {
        const { slug } = req.params;
        const problem = await prisma.problem.findUnique({
            where: { slug },
            include: {
                testCases: { where: { isHidden: false }, select: { id: true, input: true, output: true, isHidden: true } }
            }
        });
        if (!problem) {
            res.status(404).json({ message: "Problem not found" });
            return;
        }
        // Only show submissions if user is authenticated
        let submissions = [];
        if (req.session.userId) {
            submissions = await prisma.submission.findMany({
                where: { userId: req.session.userId, problemId: problem.id },
                orderBy: { createdAt: "desc" },
                take: 20,
                select: {
                    id: true,
                    language: true,
                    verdict: true,
                    executionTimeMs: true,
                    mode: true,
                    createdAt: true
                }
            });
        }
        res.json({ problem, submissions });
    }
    catch (error) {
        next(error);
    }
});
export default router;
