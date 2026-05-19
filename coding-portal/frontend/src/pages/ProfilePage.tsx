import AppShell from "../components/AppShell";
import { useOIDCAuth } from "../context/OIDCAuthContext";

function formatSocialLabel(value: string, site: "linkedin" | "github") {
  try {
    const url = new URL(value);
    const hostname = url.hostname.replace(/^www\./, "");

    if (site === "linkedin" && hostname === "linkedin.com") {
      return url.pathname.split("/").filter(Boolean).at(1) || "Profile";
    }

    if (site === "github" && hostname === "github.com") {
      return url.pathname.split("/").filter(Boolean).at(0) || "Profile";
    }

    return value.replace(/^https?:\/\//, "");
  } catch {
    return value;
  }
}

export default function ProfilePage() {
  const { user } = useOIDCAuth();

  const avatarUrl = user?.profileImage || null;
  const displayName = user?.firstName && user?.lastName
    ? `${user.firstName} ${user.lastName}`
    : user?.name || "User";
  const initials = (displayName || "U")
    .split(" ")
    .map((w) => w[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);

  if (!user) {
    return (
      <AppShell>
        <div className="page">
          <div className="card" style={{ textAlign: "center", padding: "3rem 2rem" }}>
            <h3 style={{ marginBottom: "0.75rem" }}>Please Login</h3>
            <p className="muted">Please login through BUILD UP PILOT to view your profile.</p>
          </div>
        </div>
      </AppShell>
    );
  }

  const FormGroup = ({ label, value }: { label: string; value?: string | number | null }) => (
    <div style={{ marginBottom: "1.5rem" }}>
      <label style={{ display: "block", color: "var(--gray)", fontSize: "0.875rem", marginBottom: "0.5rem", fontWeight: 500 }}>
        {label}
      </label>
      <div
        style={{
          padding: "0.75rem 1rem",
          background: "var(--card-alt, rgba(255,255,255,0.03))",
          border: "1px solid var(--border)",
          borderRadius: "8px",
          minHeight: "42px",
          color: value ? "var(--text)" : "var(--gray)",
          display: "flex",
          alignItems: "center",
          wordBreak: "break-word"
        }}
      >
        {value || "Not provided"}
      </div>
    </div>
  );

  const SocialGroup = ({ label, value, site }: { label: string; value?: string | null; site: "linkedin" | "github" }) => (
    <div style={{ marginBottom: "1.5rem" }}>
      <label style={{ display: "block", color: "var(--gray)", fontSize: "0.875rem", marginBottom: "0.5rem", fontWeight: 500 }}>
        {label}
      </label>
      <div
        style={{
          padding: "0.75rem 1rem",
          background: "var(--card-alt, rgba(255,255,255,0.03))",
          border: "1px solid var(--border)",
          borderRadius: "8px",
          minHeight: "42px",
          display: "flex",
          alignItems: "center",
          gap: "0.5rem"
        }}
      >
        {value ? (
          <>
            {site === "linkedin" && (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" style={{ flexShrink: 0, color: "#0a66c2" }}>
                <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.225 0h.003z" />
              </svg>
            )}
            {site === "github" && (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" style={{ flexShrink: 0 }}>
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-"/>
              </svg>
            )}
            <a href={value} target="_blank" rel="noopener noreferrer" style={{ color: "var(--accent)", textDecoration: "none" }}>
              {formatSocialLabel(value, site)}
            </a>
          </>
        ) : (
          <span style={{ color: "var(--gray)" }}>Not provided</span>
        )}
      </div>
    </div>
  );

  return (
    <AppShell>
      <div className="page" style={{ maxWidth: "900px", margin: "0 auto", paddingBottom: "4rem" }}>
        <div style={{ marginBottom: "2rem" }}>
          <h1 style={{ fontSize: "2rem", margin: "0 0 0.5rem 0", fontWeight: 700 }}>Profile Information</h1>
          <p className="muted" style={{ margin: 0 }}>Review your personal information and skills synced from Build Up Pilot</p>
        </div>

        <div className="card" style={{ padding: "2rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "1.5rem", marginBottom: "2.5rem", paddingBottom: "2rem", borderBottom: "1px solid var(--border)" }}>
            {avatarUrl ? (
              <img
                src={avatarUrl}
                alt={displayName}
                style={{
                  width: 90,
                  height: 90,
                  borderRadius: "50%",
                  objectFit: "cover",
                  border: "3px solid var(--accent)",
                  flexShrink: 0
                }}
                onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
              />
            ) : (
              <span
                style={{
                  width: 90,
                  height: 90,
                  borderRadius: "50%",
                  background: "var(--accent)",
                  color: "var(--bg)",
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "2.25rem",
                  fontWeight: 700,
                  flexShrink: 0
                }}
              >
                {initials}
              </span>
            )}
            <div>
              <h2 style={{ margin: "0 0 0.25rem 0", fontSize: "1.5rem" }}>{displayName}</h2>
              <p className="muted" style={{ margin: "0 0 0.5rem 0" }}>{user.email}</p>
              <div style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
                {user.studentId && (
                  <span style={{ fontSize: "0.875rem", color: "var(--accent)", background: "rgba(var(--accent-rgb), 0.1)", padding: "0.2rem 0.6rem", borderRadius: "4px" }}>
                    <strong>ID:</strong> {user.studentId}
                  </span>
                )}
                <span className="status-pill solved" style={{ margin: 0 }}>
                  Solved: {user.totalProblemsSolved ?? 0}
                </span>
              </div>
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "0 1.5rem" }}>
            <FormGroup label="First Name" value={user.firstName} />
            <FormGroup label="Last Name" value={user.lastName} />
          </div>

          <FormGroup label="Phone Number" value={user.phone} />
          <FormGroup label="Profession (What you want to become)" value={user.profession} />

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "0 1.5rem" }}>
            <FormGroup label="College/University" value={user.college} />
            <FormGroup label="Branch" value={user.branch} />
          </div>

          <FormGroup label="Graduation Year" value={user.graduationYear} />

          <div style={{ marginBottom: "1.5rem" }}>
            <label style={{ display: "block", color: "var(--gray)", fontSize: "0.875rem", marginBottom: "0.5rem", fontWeight: 500 }}>
              Skills
            </label>
            <div
              style={{
                padding: "0.75rem 1rem",
                background: "var(--card-alt, rgba(255,255,255,0.03))",
                border: "1px solid var(--border)",
                borderRadius: "8px",
                minHeight: "42px",
              }}
            >
              {user.skills ? (
                <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
                  {user.skills.split(",").map((s) => (
                    <span key={s} className="tag-chip" style={{ margin: 0 }}>{s.trim()}</span>
                  ))}
                </div>
              ) : (
                <span style={{ color: "var(--gray)" }}>Not provided</span>
              )}
            </div>
          </div>

          <FormGroup label="Location" value={user.location} />

          <div style={{ marginBottom: "1.5rem" }}>
            <label style={{ display: "block", color: "var(--gray)", fontSize: "0.875rem", marginBottom: "0.5rem", fontWeight: 500 }}>
              Bio
            </label>
            <div
              style={{
                padding: "0.75rem 1rem",
                background: "var(--card-alt, rgba(255,255,255,0.03))",
                border: "1px solid var(--border)",
                borderRadius: "8px",
                minHeight: "80px",
                color: user.bio ? "var(--text)" : "var(--gray)",
                lineHeight: 1.6
              }}
            >
              {user.bio || "Not provided"}
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "0 1.5rem" }}>
            <SocialGroup label="LinkedIn URL" value={user.linkedin} site="linkedin" />
            <SocialGroup label="GitHub URL" value={user.github} site="github" />
          </div>
          
          <div style={{ marginTop: "1rem", paddingTop: "1.5rem", borderTop: "1px solid var(--border)" }}>
            <h3 style={{ margin: "0 0 1rem 0", fontSize: "1.2rem" }}>Language-wise Accepted Submissions</h3>
            <div className="language-stat-grid">
              {user.languageStats && user.languageStats.length > 0 ? (
                user.languageStats.map((s: any) => (
                  <div key={s.language} className="language-stat" style={{ background: "var(--card-alt, rgba(255,255,255,0.03))", border: "1px solid var(--border)" }}>
                    <span className="lang-chip">{s.language}</span>
                    <strong>{s.acceptedSubmissions}</strong>
                  </div>
                ))
              ) : (
                <p className="muted" style={{ margin: 0 }}>No accepted submissions yet. Start solving problems to see your stats!</p>
              )}
            </div>
          </div>

          <div style={{ marginTop: "2rem", paddingTop: "1.5rem", borderTop: "1px solid var(--border)", textAlign: "center" }}>
            <p style={{ color: "var(--gray)", fontSize: "0.875rem", margin: 0 }}>
              To update this information, please edit your profile on the <a href="http://localhost:5002/student/profile" style={{ color: "var(--accent)", textDecoration: "underline" }}>Build Up Pilot Portal</a> and log in again to sync.
            </p>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
