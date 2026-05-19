import { Language, SubmissionMode, Verdict } from "@prisma/client";
import { Router } from "express";
import { prisma } from "../config/prisma.js";
import { requireAuth } from "../middleware/auth.js";
const router = Router();
router.get("/me", requireAuth, async (req, res, next) => {
    try {
        const userId = req.session.userId;
        const user = await prisma.user.findUnique({
            where: { id: userId },
            select: {
                id: true,
                name: true,
                firstName: true,
                lastName: true,
                email: true,
                createdAt: true,
                studentId: true,
                profileImage: true,
                phone: true,
                profession: true,
                college: true,
                branch: true,
                graduationYear: true,
                skills: true,
                bio: true,
                location: true,
                linkedin: true,
                github: true,
                buildupUid: true
            }
        });
        if (!user) {
            res.status(404).json({ message: "User not found" });
            return;
        }
        const solvedCount = await prisma.userSolvedProblem.count({ where: { userId } });
        const languageStats = await Promise.all(Object.values(Language).map(async (lang) => {
            const accepted = await prisma.submission.count({
                where: { userId, language: lang, verdict: Verdict.ACCEPTED, mode: SubmissionMode.SUBMIT }
            });
            return { language: lang, acceptedSubmissions: accepted };
        }));
        res.json({ user: { ...user, totalProblemsSolved: solvedCount, languageStats } });
    }
    catch (error) {
        next(error);
    }
});
export default router;
