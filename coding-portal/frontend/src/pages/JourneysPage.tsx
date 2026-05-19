import { useQuery } from "@tanstack/react-query";
import AppShell from "../components/AppShell";
import { api } from "../api/client";
import { Journey } from "../types";

export default function JourneysPage() {
  const query = useQuery({
    queryKey: ["journeys"],
    queryFn: async () => {
      const { data } = await api.get("/journeys");
      return data.journeys as Journey[];
    }
  });

  return (
    <AppShell>
      <div className="page">
        <div className="hero">
          <h1>Learning Journeys</h1>
          <p>Follow structured tracks and unlock consistent progress.</p>
        </div>
        <div className="journey-grid">
          {query.data?.map((j) => (
            <article className="card journey-card" key={j.id}>
              <div className="journey-head">
                <h3>{j.title}</h3>
                <span className="status-pill solved">{j.progressPercent}%</span>
              </div>
              <p className="muted">{j.description}</p>
              <p>{j.solvedProblems}/{j.totalProblems} solved</p>
              <div className="progress">
                <div className="progress-fill" style={{ width: `${j.progressPercent}%` }} />
              </div>
              <div className="journey-problems">
                {j.problems.map((p) => (
                  <div key={p.id} className="journey-problem-row">
                    <span>{p.orderIndex}. {p.title}</span>
                    <span className={`status-pill ${p.solved ? "solved" : "pending"}`}>{p.solved ? "Solved" : "Pending"}</span>
                  </div>
                ))}
              </div>
            </article>
          ))}
        </div>
      </div>
    </AppShell>
  );
}
