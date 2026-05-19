export type Difficulty = "EASY" | "MEDIUM" | "HARD";
export type Language = "C" | "CPP" | "PYTHON" | "JAVA" | "JAVASCRIPT" | "HTML" | "CSS";
export type Verdict =
  | "ACCEPTED"
  | "WRONG_ANSWER"
  | "RUNTIME_ERROR"
  | "COMPILATION_ERROR"
  | "TIME_LIMIT_EXCEEDED"
  | "INTERNAL_ERROR";

export interface User {
  id: string;
  name: string;
  firstName?: string | null;
  lastName?: string | null;
  email: string;
  role: "USER" | "ADMIN";
  createdAt?: string;
  totalProblemsSolved?: number;
  languageStats?: { language: Language; acceptedSubmissions: number }[];
  studentId?: string | null;
  profileImage?: string | null;
  phone?: string | null;
  profession?: string | null;
  college?: string | null;
  branch?: string | null;
  graduationYear?: number | null;
  skills?: string | null;
  bio?: string | null;
  location?: string | null;
  linkedin?: string | null;
  github?: string | null;
  buildupUid?: number | null;
}

export interface Problem {
  id: string;
  slug: string;
  title: string;
  difficulty: Difficulty;
  tags: string[];
  supportedLanguages: Language[];
  solved?: boolean;
  statement?: string;
  inputFormat?: string;
  outputFormat?: string;
  constraints?: string;
  sampleInput?: string;
  sampleOutput?: string;
  explanation?: string;
  starterCodes?: Record<string, string>;
  testCases?: { id: string; input: string; output: string; isHidden: boolean }[];
}

export interface Submission {
  id: string;
  language: Language;
  verdict: Verdict;
  executionTimeMs: number;
  mode: "RUN" | "SUBMIT";
  createdAt: string;
  problem?: { id: string; slug: string; title: string; difficulty: Difficulty };
}

export interface Journey {
  id: string;
  slug: string;
  title: string;
  description: string;
  totalProblems: number;
  solvedProblems: number;
  progressPercent: number;
  problems: (Problem & { orderIndex: number; solved: boolean })[];
}
