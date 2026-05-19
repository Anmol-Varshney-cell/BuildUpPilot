import { Router } from "express";
import { z } from "zod";
import { prisma } from "../config/prisma.js";
import { requireAuth } from "../middleware/auth.js";
import axios from "axios";

const router = Router();

// Simple OIDC Configuration
const OIDC_CONFIG = {
  issuer: "http://localhost:5000",
  clientId: "coding-spirit-client",
  clientSecret: "coding-spirit-secret",
  redirectUri: "http://localhost:5175/auth/callback",
  scope: "openid profile email"
};

const callbackSchema = z.object({
  code: z.string(),
  state: z.string().optional()
});

// Simple OIDC Authorization callback
router.post("/callback", async (req, res, next) => {
  try {
    const { code, state } = callbackSchema.parse(req.body);

    // Exchange authorization code for tokens
    const tokenResponse = await axios.post(`${OIDC_CONFIG.issuer}/oauth/token`, 
      new URLSearchParams({
        grant_type: "authorization_code",
        code: code,
        redirect_uri: OIDC_CONFIG.redirectUri,
        client_id: OIDC_CONFIG.clientId,
        client_secret: OIDC_CONFIG.clientSecret
      }),
      {
        headers: {
          "Content-Type": "application/x-www-form-urlencoded"
        }
      }
    );

    const { access_token, id_token } = tokenResponse.data;

    // Parse simple ID token (not real JWT, but functional)
    const [payloadB64, signature] = id_token.split('.');
    const payload = JSON.parse(Buffer.from(payloadB64 + '==', 'base64').toString('utf-8'));
    
    // Find or create user in database
    let user = await prisma.user.findUnique({ 
      where: { email: payload.email } 
    });

    if (!user) {
      user = await prisma.user.create({
        data: {
          name: payload.name || "User",
          email: payload.email,
          passwordHash: `oidc_${payload.sub}_${Date.now()}`, // Dummy password for OIDC users
          role: "USER"
        }
      });
    } else if (user.name !== (payload.name || "User")) {
      user = await prisma.user.update({
        where: { id: user.id },
        data: { name: payload.name || "User" }
      });
    }

    // Create session
    req.session.userId = user.id;
    req.session.role = user.role;
    req.session.oidcAccessToken = access_token;

    res.json({ 
      user: { 
        id: user.id, 
        name: user.name, 
        email: user.email, 
        role: user.role 
      },
      tokens: {
        accessToken: access_token,
        idToken: id_token
      }
    });

  } catch (error) {
    console.error("OIDC callback error:", error);
    if (axios.isAxiosError(error)) {
      res.status(400).json({ 
        message: "OIDC token exchange failed", 
        error: error.response?.data || error.message 
      });
    } else {
      next(error);
    }
  }
});

// Get OIDC user info
router.get("/userinfo", requireAuth, async (req, res, next) => {
  try {
    const accessToken = (req.session as any).oidcAccessToken;
    if (!accessToken) {
      res.status(401).json({ message: "No access token available" });
      return;
    }

    const userInfoResponse = await axios.get(`${OIDC_CONFIG.issuer}/oauth/userinfo`,
      {
        headers: {
          "Authorization": `Bearer ${accessToken}`
        }
      }
    );

    res.json(userInfoResponse.data);

  } catch (error) {
    console.error("OIDC userinfo error:", error);
    if (axios.isAxiosError(error)) {
      res.status(400).json({ 
        message: "Failed to get user info", 
        error: error.response?.data || error.message 
      });
    } else {
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

  } catch (error) {
    next(error);
  }
});

// OIDC discovery
router.get("/discovery", async (req, res, next) => {
  try {
    const response = await axios.get(`${OIDC_CONFIG.issuer}/.well-known/openid-configuration`);
    res.json(response.data);
  } catch (error) {
    console.error("OIDC discovery error:", error);
    if (axios.isAxiosError(error)) {
      res.status(400).json({ 
        message: "Failed to get OIDC discovery", 
        error: error.response?.data || error.message 
      });
    } else {
      next(error);
    }
  }
});

export default router;
