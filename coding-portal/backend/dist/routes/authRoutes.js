import { Router } from "express";
import { Role } from "@prisma/client";
import { z } from "zod";
import crypto from "crypto";
import { prisma } from "../config/prisma.js";
import { comparePassword, hashPassword } from "../utils/password.js";
import { requireAuth } from "../middleware/auth.js";
import { validateBody } from "../middleware/validate.js";
import { env } from "../config/env.js";
const router = Router();
const registerSchema = z.object({
    name: z.string().min(2).max(80),
    email: z.string().email(),
    password: z.string().min(6).max(100)
});
const loginSchema = z.object({
    email: z.string().email(),
    password: z.string().min(6).max(100)
});
const ssoSchema = z.object({
    token: z.string().min(10)
});
function decodeBase64Url(value) {
    const normalized = value.replace(/-/g, "+").replace(/_/g, "/");
    const padded = normalized + "=".repeat((4 - (normalized.length % 4)) % 4);
    return Buffer.from(padded, "base64").toString("utf-8");
}
function verifySsoToken(token) {
    const [payloadB64, signature] = token.split(".");
    if (!payloadB64 || !signature) {
        return { payload: null, reason: "missing_parts" };
    }
    const candidateSecrets = Array.from(new Set([
        env.ssoSharedSecret,
        process.env.SSO_SHARED_SECRET,
        process.env.SESSION_SECRET,
        "build-up-secret-key-2024"
    ].filter(Boolean)));
    const signatureValid = candidateSecrets.some((secret) => {
        const expected = crypto.createHmac("sha256", secret).update(payloadB64).digest("hex");
        return expected === signature;
    });
    if (!signatureValid) {
        return { payload: null, reason: "signature_mismatch" };
    }
    try {
        const parsed = JSON.parse(decodeBase64Url(payloadB64));
        if (!parsed?.email)
            return { payload: null, reason: "missing_email" };
        if (!parsed?.name)
            return { payload: null, reason: "missing_name" };
        if (!parsed?.exp)
            return { payload: null, reason: "missing_exp" };
        if (Number(parsed.exp) < Math.floor(Date.now() / 1000)) {
            return { payload: null, reason: "expired" };
        }
        return { payload: parsed };
    }
    catch (error) {
        return { payload: null, reason: `payload_parse_failed:${error instanceof Error ? error.message : "unknown"}` };
    }
}
router.post("/register", validateBody(registerSchema), async (req, res, next) => {
    try {
        const { name, email, password } = req.body;
        const existing = await prisma.user.findUnique({ where: { email } });
        if (existing) {
            res.status(409).json({ message: "Email already in use" });
            return;
        }
        const user = await prisma.user.create({
            data: {
                name,
                email,
                passwordHash: await hashPassword(password),
                role: Role.USER
            },
            select: { id: true, name: true, email: true, role: true }
        });
        req.session.userId = user.id;
        req.session.role = user.role;
        res.status(201).json({ user });
    }
    catch (error) {
        next(error);
    }
});
router.post("/login", validateBody(loginSchema), async (req, res, next) => {
    try {
        const { email, password } = req.body;
        const user = await prisma.user.findUnique({ where: { email } });
        if (!user) {
            res.status(401).json({ message: "Invalid email or password" });
            return;
        }
        const ok = await comparePassword(password, user.passwordHash);
        if (!ok) {
            res.status(401).json({ message: "Invalid email or password" });
            return;
        }
        req.session.userId = user.id;
        req.session.role = user.role;
        res.json({ user: { id: user.id, name: user.name, email: user.email, role: user.role } });
    }
    catch (error) {
        next(error);
    }
});
router.post("/sso", validateBody(ssoSchema), async (req, res, next) => {
    try {
        const { token } = req.body;
        const { payload, reason } = verifySsoToken(token);
        if (!payload) {
            console.warn("[SSO] Token rejected", {
                reason,
                tokenPreview: typeof token === "string" ? token.slice(0, 32) : "invalid"
            });
            res.status(401).json({ message: "Invalid or expired SSO token", reason });
            return;
        }
        // Find or create user in coding portal database, syncing profile data from BuildUp Pilot
        const userSelect = {
            id: true, name: true, firstName: true, lastName: true, email: true, role: true,
            studentId: true, profileImage: true, phone: true, profession: true,
            college: true, branch: true, graduationYear: true, skills: true, bio: true,
            location: true, linkedin: true, github: true, buildupUid: true
        };
        const existing = await prisma.user.findUnique({ where: { email: payload.email }, select: userSelect });
        const profileData = {
            name: String(payload.name),
            firstName: payload.firstName ? String(payload.firstName) : null,
            lastName: payload.lastName ? String(payload.lastName) : null,
            studentId: payload.studentId ? String(payload.studentId) : null,
            buildupUid: payload.uid ? Number(payload.uid) : null,
            profileImage: payload.profileImage ? String(payload.profileImage) : null,
            phone: payload.phone ? String(payload.phone) : null,
            profession: payload.profession ? String(payload.profession) : null,
            college: payload.college ? String(payload.college) : null,
            branch: payload.branch ? String(payload.branch) : null,
            graduationYear: payload.graduationYear ? Number(payload.graduationYear) : null,
            skills: payload.skills ? String(payload.skills) : null,
            bio: payload.bio ? String(payload.bio) : null,
            location: payload.location ? String(payload.location) : null,
            linkedin: payload.linkedin ? String(payload.linkedin) : null,
            github: payload.github ? String(payload.github) : null,
        };
        let user;
        if (!existing) {
            user = await prisma.user.create({
                data: {
                    ...profileData,
                    email: payload.email,
                    passwordHash: `sso_${payload.uid || 0}_${Date.now()}`,
                    role: Role.USER
                },
                select: userSelect
            });
        }
        else {
            user = await prisma.user.update({
                where: { id: existing.id },
                data: profileData,
                select: userSelect
            });
        }
        req.session.userId = user.id;
        req.session.role = user.role;
        res.json({ user });
    }
    catch (error) {
        next(error);
    }
});
router.post("/logout", requireAuth, (req, res) => {
    req.session.destroy(() => {
        res.clearCookie("coding.sid");
        res.json({ message: "Logged out" });
    });
});
router.get("/test-auth", (req, res) => {
    res.json({
        authenticated: !!req.session.userId,
        userId: req.session.userId || null,
        role: req.session.role || null,
        sessionId: req.sessionID || null
    });
});
router.get("/me", requireAuth, async (req, res, next) => {
    try {
        const user = await prisma.user.findUnique({
            where: { id: req.session.userId },
            select: { id: true, name: true, email: true, role: true, createdAt: true, profileImage: true, phone: true, college: true, branch: true, graduationYear: true, skills: true, location: true, linkedin: true, github: true, buildupUid: true }
        });
        if (!user) {
            res.status(404).json({ message: "User not found" });
            return;
        }
        res.json({ user });
    }
    catch (error) {
        next(error);
    }
});
export default router;
