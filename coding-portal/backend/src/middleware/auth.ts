import { NextFunction, Request, Response } from "express";
import { Role } from "@prisma/client";

export function requireAuth(req: Request, res: Response, next: NextFunction): void {
  if (!req.session.userId) {
    res.status(401).json({ message: "Unauthorized" });
    return;
  }
  next();
}

export function requireAdmin(req: Request, res: Response, next: NextFunction): void {
  if (!req.session.userId) {
    res.status(401).json({ message: "Unauthorized" });
    return;
  }
  if (req.session.role !== Role.ADMIN) {
    res.status(403).json({ message: "Forbidden" });
    return;
  }
  next();
}
