import { Difficulty, Language } from "@prisma/client";
import { Router } from "express";
import { z } from "zod";
import { prisma } from "../config/prisma.js";
import { requireAdmin, requireAuth } from "../middleware/auth.js";
import { validateBody } from "../middleware/validate.js";
const router = Router();
const testCaseSchema = z.object({
    input: z.string(),
    output: z.string(),
    isHidden: z.boolean()
});
const problemSchema = z.object({
    slug: z.string().min(2),
    title: z.string().min(3),
    difficulty: z.nativeEnum(Difficulty),
    tags: z.array(z.string()).min(1),
    supportedLanguages: z.array(z.nativeEnum(Language)).min(1),
    statement: z.string().min(10),
    inputFormat: z.string().min(3),
    outputFormat: z.string().min(3),
    constraints: z.string().min(3),
    sampleInput: z.string().min(1),
    sampleOutput: z.string().min(1),
    explanation: z.string().min(1),
    starterCodes: z.record(z.string()),
    timeLimitMs: z.number().int().positive(),
    memoryLimitMb: z.number().int().positive(),
    testCases: z.array(testCaseSchema).min(1)
});
router.use(requireAuth, requireAdmin);
router.post("/problems", validateBody(problemSchema), async (req, res, next) => {
    try {
        const body = req.body;
        const problem = await prisma.problem.create({
            data: {
                slug: body.slug,
                title: body.title,
                difficulty: body.difficulty,
                tags: body.tags,
                supportedLanguages: body.supportedLanguages,
                statement: body.statement,
                inputFormat: body.inputFormat,
                outputFormat: body.outputFormat,
                constraints: body.constraints,
                sampleInput: body.sampleInput,
                sampleOutput: body.sampleOutput,
                explanation: body.explanation,
                starterCodes: body.starterCodes,
                timeLimitMs: body.timeLimitMs,
                memoryLimitMb: body.memoryLimitMb,
                testCases: { create: body.testCases }
            }
        });
        res.status(201).json({ problem });
    }
    catch (error) {
        next(error);
    }
});
router.put("/problems/:id", validateBody(problemSchema), async (req, res, next) => {
    try {
        const { id } = req.params;
        const body = req.body;
        const updated = await prisma.problem.update({
            where: { id },
            data: {
                slug: body.slug,
                title: body.title,
                difficulty: body.difficulty,
                tags: body.tags,
                supportedLanguages: body.supportedLanguages,
                statement: body.statement,
                inputFormat: body.inputFormat,
                outputFormat: body.outputFormat,
                constraints: body.constraints,
                sampleInput: body.sampleInput,
                sampleOutput: body.sampleOutput,
                explanation: body.explanation,
                starterCodes: body.starterCodes,
                timeLimitMs: body.timeLimitMs,
                memoryLimitMb: body.memoryLimitMb,
                testCases: {
                    deleteMany: {},
                    create: body.testCases
                }
            },
            include: { testCases: true }
        });
        res.json({ problem: updated });
    }
    catch (error) {
        next(error);
    }
});
router.delete("/problems/:id", async (req, res, next) => {
    try {
        await prisma.problem.delete({ where: { id: req.params.id } });
        res.json({ message: "Problem deleted" });
    }
    catch (error) {
        next(error);
    }
});
const testCaseUploadSchema = z.object({
    testCases: z.array(testCaseSchema).min(1)
});
router.post("/problems/:id/test-cases", validateBody(testCaseUploadSchema), async (req, res, next) => {
    try {
        const { id } = req.params;
        const { testCases } = req.body;
        await prisma.testCase.deleteMany({ where: { problemId: id } });
        await prisma.testCase.createMany({
            data: testCases.map((t) => ({ ...t, problemId: id }))
        });
        res.json({ message: "Test cases updated" });
    }
    catch (error) {
        next(error);
    }
});
export default router;
