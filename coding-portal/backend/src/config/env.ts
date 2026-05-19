import dotenv from "dotenv";

dotenv.config();

function requireEnv(key: string, fallback?: string): string {
  const value = process.env[key] ?? fallback;
  if (!value) {
    throw new Error(`Missing environment variable: ${key}`);
  }
  return value;
}

export const env = {
  nodeEnv: process.env.NODE_ENV ?? "development",
  port: Number(process.env.PORT ?? 4000),
  frontendUrl: process.env.FRONTEND_URL ?? "http://localhost:5173",
  dbUrl: requireEnv("DATABASE_URL"),
  sessionSecret: requireEnv("SESSION_SECRET"),
  judgeUrl: process.env.JUDGE_URL ?? "http://localhost:5001",
  ssoSharedSecret: process.env.SSO_SHARED_SECRET ?? process.env.SESSION_SECRET ?? "build-up-secret-key-2024"
};
