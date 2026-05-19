import { Router } from "express";
import { prisma } from "../config/prisma.js";
import { requireAuth } from "../middleware/auth.js";
const router = Router();
router.get("/", requireAuth, async (req, res, next) => {
    try {
        const userId = req.session.userId;
        const journeys = await prisma.journey.findMany({
            include: {
                problems: {
                    include: {
                        problem: { select: { id: true, slug: true, title: true, difficulty: true } }
                    },
                    orderBy: { orderIndex: "asc" }
                }
            },
            orderBy: { title: "asc" }
        });
        const solved = await prisma.userSolvedProblem.findMany({
            where: { userId },
            select: { problemId: true }
        });
        const solvedSet = new Set(solved.map((s) => s.problemId));
        const payload = journeys.map((journey) => {
            const total = journey.problems.length;
            const solvedCount = journey.problems.filter((jp) => solvedSet.has(jp.problemId)).length;
            return {
                id: journey.id,
                slug: journey.slug,
                title: journey.title,
                description: journey.description,
                totalProblems: total,
                solvedProblems: solvedCount,
                progressPercent: total === 0 ? 0 : Math.round((solvedCount / total) * 100),
                problems: journey.problems.map((jp) => ({
                    ...jp.problem,
                    orderIndex: jp.orderIndex,
                    solved: solvedSet.has(jp.problemId)
                }))
            };
        });
        res.json({ journeys: payload });
    }
    catch (error) {
        next(error);
    }
});
export default router;
