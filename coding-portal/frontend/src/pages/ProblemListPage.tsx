import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import AppShell from "../components/AppShell";
import { api } from "../api/client";
import { Difficulty, Language, Problem } from "../types";

export default function ProblemListPage() {
  const [difficulty, setDifficulty] = useState<"" | Difficulty>("");
  const [tag, setTag] = useState("");
  const [language, setLanguage] = useState<"" | Language>("");
  const [q, setQ] = useState("");

  const queryParams = useMemo(() => {
    const params: Record<string, string> = {};
    if (difficulty) params.difficulty = difficulty;
    if (tag.trim()) params.tag = tag.trim();
    if (language) params.language = language;
    if (q.trim()) params.q = q.trim();
    return params;
  }, [difficulty, tag, language, q]);

  const query = useQuery({
    queryKey: ["problems", queryParams],
    queryFn: async () => {
      const response = await api.get("/problems", { params: queryParams });
      // Handle both response formats: {problems: [...]} or direct array
      return response.data.problems || response.data || [] as Problem[];
    },
    retry: 2,
    retryDelay: 1000
  });

  return (
    <AppShell>
      <div className="page">
        <div className="hero">
          <h1>Daily Coding Practice</h1>
          <p>Sharpen DSA and language fundamentals with structured challenges.</p>
        </div>

        <div className="filters">
          <input placeholder="Search by title/keyword" value={q} onChange={(e) => setQ(e.target.value)} />
          <select value={difficulty} onChange={(e) => setDifficulty(e.target.value as any)}>
            <option value="">All difficulty</option>
            <option value="EASY">Easy</option>
            <option value="MEDIUM">Medium</option>
            <option value="HARD">Hard</option>
          </select>
          <input placeholder="Tag e.g. Arrays" value={tag} onChange={(e) => setTag(e.target.value)} />
          <select value={language} onChange={(e) => setLanguage(e.target.value as any)}>
            <option value="">All languages</option>
            <option value="C">C</option>
            <option value="CPP">C++</option>
            <option value="PYTHON">Python</option>
            <option value="JAVA">Java</option>
            <option value="JAVASCRIPT">JavaScript</option>
            <option value="HTML">HTML</option>
            <option value="CSS">CSS</option>
          </select>
        </div>

        {query.isLoading && <p>Loading problems...</p>}

        {query.data && query.data.length > 0 && (
          <div className="problem-grid">
            {query.data.map((problem: Problem) => (
              <article key={problem.id} className="problem-card">
                <div className="problem-card-top">
                  <span className={`difficulty ${problem.difficulty.toLowerCase()}`}>{problem.difficulty}</span>
                  <span className={`status-pill ${problem.solved ? "solved" : "pending"}`}>
                    {problem.solved ? "Solved" : "Pending"}
                  </span>
                </div>
                <h3>
                  <Link to={`/problems/${problem.slug}`}>{problem.title}</Link>
                </h3>
                <div className="tag-row">
                  {problem.tags?.slice(0, 4).map((t: string) => (
                    <span key={t} className="tag-chip">{t}</span>
                  ))}
                </div>
                <div className="lang-row">
                  {problem.supportedLanguages?.map((l: string) => (
                    <span key={l} className="lang-chip">{l}</span>
                  ))}
                </div>
              </article>
            ))}
          </div>
        )}
        {query.data && query.data.length === 0 && (
          <div className="card">
            <h3>No problems match these filters</h3>
            <p className="muted">Try removing one or two filters, or correct spelling in tag/search (for example, use <strong>Arrays</strong>).</p>
          </div>
        )}
      </div>
    </AppShell>
  );
}
