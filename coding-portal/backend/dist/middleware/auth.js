import { Role } from "@prisma/client";
export function requireAuth(req, res, next) {
    if (!req.session.userId) {
        res.status(401).json({ message: "Unauthorized" });
        return;
    }
    next();
}
export function requireAdmin(req, res, next) {
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
