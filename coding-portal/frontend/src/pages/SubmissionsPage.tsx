import { useState } from "react";
import AppShell from "../components/AppShell";
import { useOIDCAuth } from "../context/OIDCAuthContext";

export default function SubmissionsPage() {
  const [verdict, setVerdict] = useState("");
  const [language, setLanguage] = useState("");
  const { user } = useOIDCAuth();

  return (
    <AppShell>
      <div className="page">
        <div className="hero">
          <h1 style={{fontFamily: 'Times New Roman'}}>Submission History</h1>
          <p style={{fontFamily: 'Times New Roman'}}>Review verdicts, language performance, and runtime trends.</p>
        </div>
        
        {user && user.name ? (
          <>
            <div className="filters">
              <select value={verdict} onChange={(e) => setVerdict(e.target.value)} style={{fontFamily: 'Times New Roman'}}>
                <option value="">All Verdicts</option>
                {["ACCEPTED", "WRONG_ANSWER", "RUNTIME_ERROR", "COMPILATION_ERROR", "TIME_LIMIT_EXCEEDED", "INTERNAL_ERROR"].map((v) => (
                  <option key={v} value={v}>{v}</option>
                ))}
              </select>
              <select value={language} onChange={(e) => setLanguage(e.target.value)} style={{fontFamily: 'Times New Roman'}}>
                <option value="">All Languages</option>
                {["C", "CPP", "PYTHON", "JAVA"].map((l) => (
                  <option key={l} value={l}>{l}</option>
                ))}
              </select>
            </div>

            <div className="card">
              <h3 style={{fontFamily: 'Times New Roman'}}>Your Submissions</h3>
              <p style={{fontFamily: 'Times New Roman'}}>Your submission history will appear here once you start solving problems.</p>
            </div>
          </>
        ) : (
          <div className="card">
            <h3 style={{fontFamily: 'Times New Roman'}}>Please Login</h3>
            <p style={{fontFamily: 'Times New Roman'}}>Please login through BUILD UP PILOT to view your submissions.</p>
          </div>
        )}
      </div>
    </AppShell>
  );
}
