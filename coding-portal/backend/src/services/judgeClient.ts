import axios from "axios";
import { Language, TestCase, Verdict } from "@prisma/client";
import { env } from "../config/env.js";

export type JudgeMode = "run" | "submit";

export interface JudgeCasePayload {
  id: string;
  input: string;
  expectedOutput: string;
  isHidden: boolean;
}

export interface JudgeRequest {
  sourceCode: string;
  language: Language;
  mode: JudgeMode;
  timeLimitMs: number;
  memoryLimitMb: number;
  testCases: JudgeCasePayload[];
}

export interface JudgeCaseResult {
  id: string;
  passed: boolean;
  verdict: Verdict;
  actualOutput: string;
  expectedOutput?: string;
  executionTimeMs: number;
  error?: string;
  isHidden: boolean;
}

export interface JudgeResponse {
  verdict: Verdict;
  executionTimeMs: number;
  testCaseResults: JudgeCaseResult[];
  compileOutput?: string;
}

export function toJudgeCases(testCases: TestCase[]): JudgeCasePayload[] {
  return testCases.map((t) => ({
    id: t.id,
    input: t.input,
    expectedOutput: t.output,
    isHidden: t.isHidden
  }));
}

export async function executeInJudge(payload: JudgeRequest): Promise<JudgeResponse> {
  const response = await axios.post<JudgeResponse>(`${env.judgeUrl}/execute`, payload, {
    timeout: 120000
  });
  return response.data;
}
