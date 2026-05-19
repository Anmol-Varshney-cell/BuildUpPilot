import { Router } from "express";
import { z } from "zod";
import { prisma } from "../config/prisma.js";
import { requireAuth } from "../middleware/auth.js";
import axios from "axios";
import jwt from "jsonwebtoken";
const router = Router();
// OIDC Configuration
const OIDC_CONFIG = {
    issuer: "http://localhost:5000",
    clientId: "coding-spirit-client",
    clientSecret: "coding-spirit-secret",
    redirectUri: "http://localhost:5173/auth/callback",
    scope: "openid profile email"
};
// Public key for JWT verification (use proper key in production)
const PUBLIC_KEY = `-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAxvBnJ9v6Q9Jp...
-----END PUBLIC KEY-----`;
const callbackSchema = z.object({
    code: z.string(),
    state: z.string().optional()
});
// OIDC Authorization callback
router.post("/callback", async (req, res, next) => {
    try {
        const { code, state } = callbackSchema.parse(req.body);
        // Exchange authorization code for tokens
        const tokenResponse = await axios.post(`${OIDC_CONFIG.issuer}/oauth/token`, new URLSearchParams({
            grant_type: "authorization_code",
            code: code,
            redirect_uri: OIDC_CONFIG.redirectUri,
            client_id: OIDC_CONFIG.clientId,
            client_secret: OIDC_CONFIG.clientSecret
        }), {
            headers: {
                "Content-Type": "application/x-www-form-urlencoded"
            }
        });
        const { access_token, id_token, refresh_token } = tokenResponse.data;
        // Verify ID token
        const decoded = jwt.verify(id_token, PUBLIC_KEY, { algorithms: ['RS256'] });
        // Find or create user in database
        let user = await prisma.user.findUnique({
            where: { email: decoded.email }
        });
        if (!user) {
            user = await prisma.user.create({
                data: {
                    name: decoded.name || decoded.preferred_username || "User",
                    email: decoded.email,
                    passwordHash: `oidc_${decoded.sub}_${Date.now()}`, // Dummy password for OIDC users
                    role: "USER"
                }
            });
        }
        else if (user.name !== (decoded.name || decoded.preferred_username)) {
            user = await prisma.user.update({
                where: { id: user.id },
                data: { name: decoded.name || decoded.preferred_username || "User" }
            });
        }
        // Create session
        req.session.userId = user.id;
        req.session.role = user.role;
        req.session.oidcAccessToken = access_token;
        req.session.oidcRefreshToken = refresh_token;
        res.json({
            user: {
                id: user.id,
                name: user.name,
                email: user.email,
                role: user.role
            },
            tokens: {
                accessToken: access_token,
                idToken: id_token,
                refreshToken: refresh_token
            }
        });
    }
    catch (error) {
        console.error("OIDC callback error:", error);
        if (axios.isAxiosError(error)) {
            res.status(400).json({
                message: "OIDC token exchange failed",
                error: error.response?.data || error.message
            });
        }
        else {
            next(error);
        }
    }
});
// Refresh OIDC tokens
router.post("/refresh", requireAuth, async (req, res, next) => {
    try {
        const refreshToken = req.session.oidcRefreshToken;
        if (!refreshToken) {
            res.status(401).json({ message: "No refresh token available" });
            return;
        }
        const tokenResponse = await axios.post(`${OIDC_CONFIG.issuer}/oauth/token`, new URLSearchParams({
            grant_type: "refresh_token",
            refresh_token: refreshToken,
            client_id: OIDC_CONFIG.clientId,
            client_secret: OIDC_CONFIG.clientSecret
        }), {
            headers: {
                "Content-Type": "application/x-www-form-urlencoded"
            }
        });
        const { access_token, refresh_token: new_refresh_token, id_token } = tokenResponse.data;
        // Update session with new tokens
        req.session.oidcAccessToken = access_token;
        if (new_refresh_token) {
            req.session.oidcRefreshToken = new_refresh_token;
        }
        res.json({
            accessToken: access_token,
            refreshToken: new_refresh_token,
            idToken: id_token
        });
    }
    catch (error) {
        console.error("OIDC refresh error:", error);
        if (axios.isAxiosError(error)) {
            res.status(400).json({
                message: "Token refresh failed",
                error: error.response?.data || error.message
            });
        }
        else {
            next(error);
        }
    }
});
// Get OIDC user info
router.get("/userinfo", requireAuth, async (req, res, next) => {
    try {
        const accessToken = req.session.oidcAccessToken;
        if (!accessToken) {
            res.status(401).json({ message: "No access token available" });
            return;
        }
        const userInfoResponse = await axios.get(`${OIDC_CONFIG.issuer}/oauth/userinfo`, {
            headers: {
                "Authorization": `Bearer ${accessToken}`
            }
        });
        res.json(userInfoResponse.data);
    }
    catch (error) {
        console.error("OIDC userinfo error:", error);
        if (axios.isAxiosError(error)) {
            res.status(400).json({
                message: "Failed to get user info",
                error: error.response?.data || error.message
            });
        }
        else {
            next(error);
        }
    }
});
// OIDC logout
router.post("/logout", requireAuth, async (req, res, next) => {
    try {
        // Clear session
        req.session.destroy((err) => {
            if (err) {
                console.error("Session destroy error:", err);
            }
            res.clearCookie("coding.sid");
            res.json({ message: "Logged out successfully" });
        });
    }
    catch (error) {
        next(error);
    }
});
// OIDC discovery
router.get("/discovery", async (req, res, next) => {
    try {
        const response = await axios.get(`${OIDC_CONFIG.issuer}/.well-known/openid-configuration`);
        res.json(response.data);
    }
    catch (error) {
        console.error("OIDC discovery error:", error);
        if (axios.isAxiosError(error)) {
            res.status(400).json({
                message: "Failed to get OIDC discovery",
                error: error.response?.data || error.message
            });
        }
        else {
            next(error);
        }
    }
});
export default router;
