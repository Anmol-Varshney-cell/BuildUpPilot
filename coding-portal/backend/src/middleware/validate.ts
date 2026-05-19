import { NextFunction, Request, Response } from "express";
import { z, ZodTypeAny } from "zod";

export function validateBody(schema: ZodTypeAny) {
  return (req: Request, res: Response, next: NextFunction): void => {
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
