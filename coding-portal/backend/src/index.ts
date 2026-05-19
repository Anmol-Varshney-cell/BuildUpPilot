import cors from "cors";
import express from "express";
import session from "express-session";
import helmet from "helmet";
import morgan from "morgan";
import apiRouter from "./routes/index.js";
import { env } from "./config/env.js";
import { errorHandler, notFound } from "./middleware/error.js";

const app = express();

app.use(helmet());
app.use(
  cors({
    origin: ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174"],
    credentials: true
  })
);
app.use(express.json({ limit: "2mb" }));
app.use(morgan("dev"));
app.use(
  session({
    name: "coding.sid",
    secret: env.sessionSecret,
    resave: false,
    saveUninitialized: false,
    cookie: {
      httpOnly: true,
      // With Vite proxy, frontend and backend are same-origin, so lax works.
      // If serving frontend directly from backend in production, keep lax.
      sameSite: "lax",
      secure: env.nodeEnv === "production",
      maxAge: 1000 * 60 * 60 * 24 * 7
    }
  })
);

app.use("/api", apiRouter);
app.use(notFound);
app.use(errorHandler);

app.listen(env.port, () => {
  console.log(`Backend running on http://localhost:${env.port}`);
});
