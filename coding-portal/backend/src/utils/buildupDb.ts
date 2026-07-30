import fs from "fs";
import path from "path";
import { DatabaseSync } from "node:sqlite";

export interface BuildUpUserRecord {
  id: number;
  email: string;
  password_hash: string;
  role: string;
  student_id: string | null;
  mobile: string | null;
  first_name: string | null;
  last_name: string | null;
  profession: string | null;
  linkedin: string | null;
  github: string | null;
}

export function findBuildUpUserByEmail(email: string): BuildUpUserRecord | null {
  try {
    // Resolve absolute path to buildup.db from project root
    const pathsToTry = [
      path.resolve(process.cwd(), "buildup.db"),
      path.resolve(process.cwd(), "..", "buildup.db"),
      path.resolve(process.cwd(), "..", "..", "buildup.db"),
      "C:\\Users\\Anmol\\OneDrive\\Desktop\\B\\buildup.db"
    ];

    const targetPath = pathsToTry.find((p) => fs.existsSync(p));

    if (!targetPath) {
      console.warn("[BuildUp Sync] buildup.db not found in paths:", pathsToTry);
      return null;
    }

    const db = new DatabaseSync(targetPath);
    const stmt = db.prepare(`
      SELECT id, email, password_hash, role, student_id, mobile, first_name, last_name, profession, linkedin, github
      FROM users WHERE LOWER(email) = LOWER(?) LIMIT 1
    `);
    const result = stmt.get(email) as BuildUpUserRecord | undefined;
    db.close();
    return result || null;
  } catch (err) {
    console.error("[BuildUp Sync] Error reading buildup.db:", err);
    return null;
  }
}
