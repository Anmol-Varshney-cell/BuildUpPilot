import { Link, NavLink } from "react-router-dom";
import { useState, useEffect } from "react";
import { useOIDCAuth } from "../context/OIDCAuthContext";

export default function AppShell({ children }: { children: React.ReactNode }) {
  const { user, loading, oidcError } = useOIDCAuth();
  const userName = user?.name || user?.email || "Guest";

  // Theme toggle
  const [theme, setTheme] = useState<"dark" | "light">(() => {
    return (localStorage.getItem("skillup_theme") as "dark" | "light") || "dark";
  });

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("skillup_theme", theme);
  }, [theme]);

  const toggleTheme = () => setTheme((t) => (t === "dark" ? "light" : "dark"));

  const avatarUrl = user?.profileImage || null;
  const initials = userName
    .split(" ")
    .map((w) => w[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);

  return (
    <div className="app-shell">
      {/* Animated background */}
      <div className="bg-blob bg-blob-1" />
      <div className="bg-blob bg-blob-2" />
      <div className="bg-grid" />

      <header className="topbar">
        <Link to="/problems" className="brand">
          SKILL UP
        </Link>

        <nav className="topnav">
          <NavLink to="/problems">Problems</NavLink>
          <NavLink to="/journeys">Journeys</NavLink>
          <NavLink to="/submissions">Submissions</NavLink>
          <NavLink to="/profile">Profile</NavLink>
        </nav>

        <div className="topbar-right">
          {/* Theme toggle */}
          <button
            className="theme-toggle"
            onClick={toggleTheme}
            aria-label="Toggle theme"
            title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          >
            {theme === "dark" ? "\u2600\uFE0F" : "\uD83C\uDF19"}
          </button>

          {loading ? (
            <span className="user-pill">Loading...</span>
          ) : user ? (
            <>
              {avatarUrl ? (
                <img
                  src={avatarUrl}
                  alt={userName}
                  className="user-avatar"
                  style={{
                    width: 32,
                    height: 32,
                    borderRadius: "50%",
                    objectFit: "cover",
                    border: "2px solid var(--accent)"
                  }}
                  onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
                />
              ) : (
                <span
                  className="user-avatar-placeholder"
                  style={{
                    width: 32,
                    height: 32,
                    borderRadius: "50%",
                    background: "var(--accent)",
                    color: "var(--bg)",
                    display: "inline-flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: "0.75rem",
                    fontWeight: 700
                  }}
                >
                  {initials}
                </span>
              )}
              <span className="user-pill">{userName}</span>
            </>
          ) : (
            <span className="user-pill" style={{ opacity: 0.7 }}>Login via Build Up Pilot</span>
          )}
          {oidcError && <span style={{ color: "#f87171", fontSize: "0.8rem" }}>{oidcError}</span>}
        </div>
      </header>

      <main>{children}</main>
    </div>
  );
}
