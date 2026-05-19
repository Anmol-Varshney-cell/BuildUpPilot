import { z } from "zod";
export function validateBody(schema) {
    return (req, res, next) => {
        const result = schema.safeParse(req.body);
        if (!result.success) {
            res.status(400).json({ message: "Validation failed", errors: result.error.flatten() });
            return;
        }
        req.body = result.data;
        next();
    };
}
export const IdParamSchema = z.object({ id: z.string().min(1) });
