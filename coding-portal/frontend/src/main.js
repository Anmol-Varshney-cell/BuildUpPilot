import "./styles.css";
import * as monaco from "monaco-editor";
import editorWorker from "monaco-editor/esm/vs/editor/editor.worker?worker";
import jsonWorker from "monaco-editor/esm/vs/language/json/json.worker?worker";
import cssWorker from "monaco-editor/esm/vs/language/css/css.worker?worker";
import htmlWorker from "monaco-editor/esm/vs/language/html/html.worker?worker";
import tsWorker from "monaco-editor/esm/vs/language/typescript/ts.worker?worker";

self.MonacoEnvironment = {
  getWorker(_, label) {
    if (label === "json") return new jsonWorker();
    if (label === "css" || label === "scss" || label === "less") return new cssWorker();
    if (label === "html" || label === "handlebars" || label === "razor") return new htmlWorker();
    if (label === "typescript" || label === "javascript") return new tsWorker();
    return new editorWorker();
  }
};

// Use relative URL so Vite proxy routes to backend (eliminates CORS/cookie issues)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";
const BUILDUP_BASE_URL =
  import.meta.env.VITE_BUILDUP_BASE_URL ||
  (window.location.port === "5173" || window.location.port === "5174"
    ? `${window.location.protocol}//${window.location.hostname}:5002`
    : window.location.origin);
const app = document.getElementById("app");

const state = {
  theme: localStorage.getItem("skillup_theme") || "dark",
  user: null,
  authLoading: true,
  oidcError: null,
  route: { name: "problems", slug: null },
  problemFilters: {
    q: "",
    difficulty: "",
    tag: "",
    language: ""
  },
  problemDetail: {
    problemSlug: null,
    language: "PYTHON",
    sourceCode: "# Write your solution\n",
    result: null,
    execError: null,
    pending: false
  },
  submissionsFilters: {
    verdict: "",
    language: ""
  }
};

let editorInstance = null;
let editorModelLanguage = "python";

function applyTheme() {
  document.documentElement.setAttribute("data-theme", state.theme);
  localStorage.setItem("skillup_theme", state.theme);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function formatMultiline(value) {
  return escapeHtml(value ?? "").replace(/\n/g, "<br>");
}

function buildUrl(path, query) {
  const url = new URL(`${API_BASE_URL}${path}`, window.location.origin);
  if (query) {
    Object.entries(query).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        url.searchParams.set(key, value);
      }
    });
  }
  return url.toString();
}

async function api(path, options = {}) {
  const { method = "GET", body, query } = options;
  const response = await fetch(buildUrl(path, query), {
    method,
    credentials: "include",
    headers: {
      Accept: "application/json",
      ...(body ? { "Content-Type": "application/json" } : {})
    },
    body: body ? JSON.stringify(body) : undefined
  });

  let data = null;
  const text = await response.text();
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = { message: text };
    }
  }

  if (!response.ok) {
    const error = new Error(
      data?.message || data?.error || `Request failed with status ${response.status}`
    );
    error.status = response.status;
    error.data = data;
    throw error;
  }

  return data;
}

async function fetchBuildUpSsoToken() {
  const response = await fetch(`${BUILDUP_BASE_URL}/api/skillup/sso-token`, {
    method: "GET",
    credentials: "include",
    headers: {
      Accept: "application/json"
    }
  });

  if (!response.ok) {
    const error = new Error(`Build Up SSO bootstrap failed with status ${response.status}`);
    error.status = response.status;
    throw error;
  }

  const contentType = response.headers.get("content-type") || "";
  if (!contentType.includes("application/json")) {
    const error = new Error("Build Up SSO bootstrap returned non-JSON response");
    error.status = 500;
    throw error;
  }

  return response.json();
}

function getInitials(name) {
  return (name || "U")
    .split(" ")
    .map((part) => part[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

function languageToMonaco(language) {
  switch (language) {
    case "CPP":
      return "cpp";
    case "JAVASCRIPT":
      return "javascript";
    case "PYTHON":
      return "python";
    case "JAVA":
      return "java";
    case "HTML":
      return "html";
    case "CSS":
      return "css";
    default:
      return "c";
  }
}

function parseRoute(pathname = window.location.pathname) {
  const cleaned = pathname.replace(/\/+$/, "") || "/";
  if (cleaned === "/" || cleaned === "/problems") return { name: "problems", slug: null };
  if (cleaned === "/journeys") return { name: "journeys", slug: null };
  if (cleaned === "/submissions") return { name: "submissions", slug: null };
  if (cleaned === "/profile") return { name: "profile", slug: null };
  const match = cleaned.match(/^\/problems\/([^/]+)$/);
  if (match) return { name: "problem-detail", slug: decodeURIComponent(match[1]) };
  return { name: "problems", slug: null };
}

function navigate(path, replace = false) {
  const method = replace ? "replaceState" : "pushState";
  window.history[method]({}, "", path);
  state.route = parseRoute(path);
  renderRoute();
}

function shellHtml(content) {
  const user = state.user;
  const userName = user?.name || user?.email || "Guest";
  const avatar = user?.profileImage
    ? `<img src="${escapeHtml(user.profileImage)}" alt="${escapeHtml(userName)}" class="user-avatar" />`
    : `<span class="user-avatar-placeholder">${escapeHtml(getInitials(userName))}</span>`;

  return `
    <div class="app-shell">
      <div class="bg-blob bg-blob-1"></div>
      <div class="bg-blob bg-blob-2"></div>
      <div class="bg-grid"></div>

      <header class="topbar">
        <a href="/problems" class="brand" data-link>SKILL UP</a>

        <nav class="topnav">
          <a href="/problems" data-link class="${state.route.name === "problems" || state.route.name === "problem-detail" ? "active" : ""}">Problems</a>
          <a href="/journeys" data-link class="${state.route.name === "journeys" ? "active" : ""}">Journeys</a>
          <a href="/submissions" data-link class="${state.route.name === "submissions" ? "active" : ""}">Submissions</a>
          <a href="/profile" data-link class="${state.route.name === "profile" ? "active" : ""}">Profile</a>
        </nav>

        <div class="topbar-right">
          <button class="theme-toggle" id="theme-toggle" aria-label="Toggle theme" title="${state.theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}">
            ${state.theme === "dark" ? "☀️" : "🌙"}
          </button>
          ${
            state.authLoading
              ? `<span class="user-pill">Loading...</span>`
              : user
                ? `${avatar}<span class="user-pill">${escapeHtml(userName)}</span>`
                : `<span class="user-pill" style="opacity:0.7;">Login via Build Up Pilot</span>`
          }
          ${state.oidcError ? `<span class="topbar-error">${escapeHtml(state.oidcError)}</span>` : ""}
        </div>
      </header>

      <main>${content}</main>
    </div>
  `;
}

function pageLoadingHtml(title, subtitle = "Loading...") {
  return `
    <div class="page">
      <div class="hero">
        <h1>${escapeHtml(title)}</h1>
        <p>${escapeHtml(subtitle)}</p>
      </div>
      <div class="card loading-card">
        <p class="loading-copy">Loading content...</p>
      </div>
    </div>
  `;
}

function pageMessageHtml(title, text) {
  return `
    <div class="page">
      <div class="card">
        <h3>${escapeHtml(title)}</h3>
        <p class="muted">${escapeHtml(text)}</p>
      </div>
    </div>
  `;
}

function renderApp(content) {
  if (editorInstance) {
    editorInstance.dispose();
    editorInstance = null;
  }
  app.innerHTML = shellHtml(content);
  applyTheme();
  attachGlobalEvents();
}

function attachGlobalEvents() {
  document.querySelectorAll("[data-link]").forEach((link) => {
    link.addEventListener("click", (event) => {
      const href = link.getAttribute("href");
      if (!href || href.startsWith("http")) return;
      event.preventDefault();
      navigate(href);
    });
  });

  const themeToggle = document.getElementById("theme-toggle");
  if (themeToggle) {
    themeToggle.addEventListener("click", () => {
      state.theme = state.theme === "dark" ? "light" : "dark";
      renderRoute();
    });
  }
}

async function initAuth() {
  state.authLoading = true;
  state.oidcError = null;
  const params = new URLSearchParams(window.location.search);
  const ssoToken = params.get("sso");

  if (ssoToken) {
    const cleanUrl = `${window.location.origin}${window.location.pathname}`;
    window.history.replaceState({}, "", cleanUrl);
    try {
      console.log("Attempting SSO login with token:", ssoToken);
      const data = await api("/auth/sso", {
        method: "POST",
        body: { token: ssoToken }
      });
      console.log("SSO login successful:", data);
      state.user = data.user;
      state.oidcError = null;
    } catch (error) {
      console.error("SSO login failed:", error);
      state.oidcError = error.message || "SSO login failed. Please try again from Build Up Pilot.";
      
      // Retry mechanism
      if (error.status === 401 || error.status === 500) {
        console.log("Retrying SSO bootstrap...");
        try {
          const bootstrap = await fetchBuildUpSsoToken();
          if (bootstrap?.token) {
            const retryData = await api("/auth/sso", {
              method: "POST",
              body: { token: bootstrap.token }
            });
            state.user = retryData.user;
            state.oidcError = null;
          }
        } catch (retryError) {
          console.error("Retry failed:", retryError);
          state.oidcError = "SSO login failed. Please refresh the page and try again.";
        }
      }
    }
  }

  if (!state.user) {
    try {
      const data = await api("/auth/me");
      state.user = data.user;
    } catch (error) {
      if (error.status === 401) {
        try {
          const bootstrap = await fetchBuildUpSsoToken();
          if (bootstrap?.token) {
            const data = await api("/auth/sso", {
              method: "POST",
              body: { token: bootstrap.token }
            });
            state.user = data.user;
          }
        } catch {
          // Build Up session is not available; keep Skill Up logged out.
        }
      } else if (!state.oidcError) {
        state.oidcError = "Unable to verify your session right now.";
      }
    }
  }

  if (state.user) {
    await enrichUserProfile();
  } else {
    state.user = null;
  }

  state.authLoading = false;
}

async function enrichUserProfile() {
  if (!state.user) return null;
  try {
    const data = await api("/profile/me");
    state.user = { ...state.user, ...data.user };
  } catch {
    // Keep the basic auth user if profile stats are unavailable.
  }
  return state.user;
}

function renderProblemsPage(problems) {
  const cards = problems.length
    ? `
      <div class="problem-grid">
        ${problems
          .map(
            (problem) => `
              <article class="problem-card">
                <div class="problem-card-top">
                  <span class="difficulty ${problem.difficulty.toLowerCase()}">${escapeHtml(problem.difficulty)}</span>
                  <span class="status-pill ${problem.solved ? "solved" : "pending"}">${problem.solved ? "Solved" : "Pending"}</span>
                </div>
                <h3><a href="/problems/${encodeURIComponent(problem.slug)}" data-link>${escapeHtml(problem.title)}</a></h3>
                <div class="tag-row">
                  ${(problem.tags || []).slice(0, 4).map((tag) => `<span class="tag-chip">${escapeHtml(tag)}</span>`).join("")}
                </div>
                <div class="lang-row">
                  ${(problem.supportedLanguages || []).map((language) => `<span class="lang-chip">${escapeHtml(language)}</span>`).join("")}
                </div>
              </article>
            `
          )
          .join("")}
      </div>
    `
    : `
      <div class="card">
        <h3>No problems match these filters</h3>
        <p class="muted">Try removing one or two filters, or correct spelling in tag or search.</p>
      </div>
    `;

  return `
    <div class="page">
      <div class="hero">
        <h1>Daily Coding Practice</h1>
        <p>Sharpen DSA and language fundamentals with structured challenges.</p>
      </div>

      <div class="filters">
        <input id="filter-q" placeholder="Search by title/keyword" value="${escapeHtml(state.problemFilters.q)}" />
        <select id="filter-difficulty">
          <option value="">All difficulty</option>
          <option value="EASY" ${state.problemFilters.difficulty === "EASY" ? "selected" : ""}>Easy</option>
          <option value="MEDIUM" ${state.problemFilters.difficulty === "MEDIUM" ? "selected" : ""}>Medium</option>
          <option value="HARD" ${state.problemFilters.difficulty === "HARD" ? "selected" : ""}>Hard</option>
        </select>
        <input id="filter-tag" placeholder="Tag e.g. Arrays" value="${escapeHtml(state.problemFilters.tag)}" />
        <select id="filter-language">
          <option value="">All languages</option>
          ${["C", "CPP", "PYTHON", "JAVA", "JAVASCRIPT", "HTML", "CSS"]
            .map((language) => `<option value="${language}" ${state.problemFilters.language === language ? "selected" : ""}>${language}</option>`)
            .join("")}
        </select>
      </div>

      ${cards}
    </div>
  `;
}

function attachProblemFilters() {
  const sync = () => {
    state.problemFilters.q = document.getElementById("filter-q")?.value || "";
    state.problemFilters.difficulty = document.getElementById("filter-difficulty")?.value || "";
    state.problemFilters.tag = document.getElementById("filter-tag")?.value || "";
    state.problemFilters.language = document.getElementById("filter-language")?.value || "";
    renderRoute();
  };

  ["filter-q", "filter-difficulty", "filter-tag", "filter-language"].forEach((id) => {
    const element = document.getElementById(id);
    if (element) {
      element.addEventListener("input", sync);
      element.addEventListener("change", sync);
    }
  });
}

function renderProblemDetailPage(problem, submissions) {
  const result = state.problemDetail.result;
  const consoleHtml = state.problemDetail.pending
    ? `<p>Running...</p>`
    : state.problemDetail.execError
      ? `<p class="error">${escapeHtml(state.problemDetail.execError)}</p>`
      : result
        ? `
          <p><strong>Verdict:</strong> <span class="status-pill ${result.verdict === "ACCEPTED" ? "solved" : "pending"}">${escapeHtml(result.verdict)}</span></p>
          <p><strong>Execution Time:</strong> ${escapeHtml(result.executionTimeMs)} ms</p>
          ${result.compileOutput ? `<pre>${escapeHtml(result.compileOutput)}</pre>` : ""}
          <div class="case-results">
            ${result.testCaseResults
              .map(
                (item) => `
                  <div class="case-item">
                    <p><strong>${escapeHtml(item.verdict)}</strong> | ${escapeHtml(item.executionTimeMs)} ms</p>
                    ${item.error ? `<pre>${escapeHtml(item.error)}</pre>` : ""}
                    <p>Actual: ${escapeHtml(item.actualOutput || "(empty)")}</p>
                    ${item.expectedOutput !== undefined ? `<p>Expected: ${escapeHtml(item.expectedOutput)}</p>` : ""}
                  </div>
                `
              )
              .join("")}
          </div>
        `
        : `<p class="muted">Run your code to inspect sample case output or submit it against hidden tests.</p>`;

  return `
    <div class="workspace">
      <section class="statement-panel">
        <div class="statement-header">
          <h2>${escapeHtml(problem.title)}</h2>
          <span class="difficulty ${problem.difficulty.toLowerCase()}">${escapeHtml(problem.difficulty)}</span>
        </div>
        <div class="tag-row">
          ${(problem.tags || []).map((tag) => `<span class="tag-chip">${escapeHtml(tag)}</span>`).join("")}
        </div>
        <article class="statement">${formatMultiline(problem.statement)}</article>
        <h4>Input</h4>
        <pre>${escapeHtml(problem.inputFormat)}</pre>
        <h4>Output</h4>
        <pre>${escapeHtml(problem.outputFormat)}</pre>
        <h4>Constraints</h4>
        <pre>${escapeHtml(problem.constraints)}</pre>
        <h4>Sample Input</h4>
        <pre>${escapeHtml(problem.sampleInput)}</pre>
        <h4>Sample Output</h4>
        <pre>${escapeHtml(problem.sampleOutput)}</pre>
        <h4>Explanation</h4>
        <pre>${escapeHtml(problem.explanation)}</pre>
      </section>

      <section class="editor-panel">
        <div class="editor-toolbar">
          <select id="problem-language">
            ${(problem.supportedLanguages || [])
              .map((language) => `<option value="${language}" ${state.problemDetail.language === language ? "selected" : ""}>${language}</option>`)
              .join("")}
          </select>
          <button class="ghost-btn" id="reset-code">Reset</button>
          <button class="action-btn" id="run-code" ${state.user ? "" : "disabled"}>${state.problemDetail.pending ? "Running..." : "Run"}</button>
          <button class="action-btn submit" id="submit-code" ${state.user ? "" : "disabled"}>${state.problemDetail.pending ? "Submitting..." : "Submit"}</button>
        </div>

        <div id="editor-host" class="editor-host"></div>
        ${state.user ? "" : `<p class="page-note">Login through Build Up Pilot to run or submit code.</p>`}

        <div class="console">
          <h4>Execution Console</h4>
          ${consoleHtml}
        </div>

        <div class="submissions-box">
          <h4>Your Recent Submissions</h4>
          <table class="table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Mode</th>
                <th>Language</th>
                <th>Verdict</th>
                <th>Exec(ms)</th>
              </tr>
            </thead>
            <tbody>
              ${
                submissions.length
                  ? submissions
                      .map(
                        (submission) => `
                          <tr>
                            <td>${escapeHtml(new Date(submission.createdAt).toLocaleString())}</td>
                            <td>${escapeHtml(submission.mode)}</td>
                            <td>${escapeHtml(submission.language)}</td>
                            <td>${escapeHtml(submission.verdict)}</td>
                            <td>${escapeHtml(submission.executionTimeMs)}</td>
                          </tr>
                        `
                      )
                      .join("")
                  : `<tr><td colspan="5" class="muted">No submissions yet for this problem.</td></tr>`
              }
            </tbody>
          </table>
        </div>
      </section>
    </div>
  `;
}

function ensureEditor(problem) {
  const host = document.getElementById("editor-host");
  if (!host) return;

  const monacoLanguage = languageToMonaco(state.problemDetail.language);
  if (!editorInstance) {
    editorInstance = monaco.editor.create(host, {
      value: state.problemDetail.sourceCode,
      language: monacoLanguage,
      theme: state.theme === "dark" ? "vs-dark" : "vs",
      minimap: { enabled: false },
      fontSize: 14,
      automaticLayout: true,
      roundedSelection: false,
      scrollBeyondLastLine: false
    });
    editorModelLanguage = monacoLanguage;
    editorInstance.onDidChangeModelContent(() => {
      state.problemDetail.sourceCode = editorInstance.getValue();
    });
  } else {
    editorInstance.setValue(state.problemDetail.sourceCode);
    monaco.editor.setTheme(state.theme === "dark" ? "vs-dark" : "vs");
    if (editorModelLanguage !== monacoLanguage) {
      monaco.editor.setModelLanguage(editorInstance.getModel(), monacoLanguage);
      editorModelLanguage = monacoLanguage;
    }
  }

  const languageSelect = document.getElementById("problem-language");
  if (languageSelect) {
    languageSelect.addEventListener("change", () => {
      state.problemDetail.language = languageSelect.value;
      state.problemDetail.sourceCode =
        problem.starterCodes?.[state.problemDetail.language] || "# Write your solution\n";
      state.problemDetail.execError = null;
      state.problemDetail.result = null;
      renderRoute();
    });
  }

  const resetButton = document.getElementById("reset-code");
  if (resetButton) {
    resetButton.addEventListener("click", () => {
      state.problemDetail.sourceCode =
        problem.starterCodes?.[state.problemDetail.language] || "# Write your solution\n";
      state.problemDetail.execError = null;
      state.problemDetail.result = null;
      renderRoute();
    });
  }

  const handleExecute = async (mode) => {
    state.problemDetail.pending = true;
    state.problemDetail.execError = null;
    state.problemDetail.result = null;
    renderRoute();
    try {
      const result = await api("/submissions/execute", {
        method: "POST",
        body: {
          problemSlug: state.route.slug,
          language: state.problemDetail.language,
          sourceCode: state.problemDetail.sourceCode,
          mode
        }
      });
      state.problemDetail.result = result;
    } catch (error) {
      state.problemDetail.execError =
        error?.data?.message || error?.message || "Execution failed. Please try again.";
    } finally {
      state.problemDetail.pending = false;
      renderRoute();
    }
  };

  const runButton = document.getElementById("run-code");
  if (runButton) runButton.addEventListener("click", () => handleExecute("run"));

  const submitButton = document.getElementById("submit-code");
  if (submitButton) submitButton.addEventListener("click", () => handleExecute("submit"));
}

function renderProfilePage(user) {
  const avatarUrl = user?.profileImage || null;
  const displayName = user?.firstName && user?.lastName
    ? `${user.firstName} ${user.lastName}`
    : user?.name || "User";
  const initials = getInitials(displayName);
  const languageStats = user?.languageStats || [];

  if (!user) {
    return pageMessageHtml("Please Login", "Please login through BUILD UP PILOT to view your profile.");
  }

  return `
    <div class="page">
      <div class="hero">
        <h1>Profile</h1>
        <p>Your student profile synced from Build Up Pilot.</p>
      </div>

      <div class="profile-grid">
        <article class="card profile-main" style="display: flex; align-items: center; gap: 1.25rem;">
          ${
            avatarUrl
              ? `<img src="${escapeHtml(avatarUrl)}" alt="${escapeHtml(displayName)}" class="profile-avatar-large" style="width: 80px; height: 80px; border-radius: 50%; object-fit: cover; border: 3px solid var(--accent); flex-shrink: 0;" onerror="this.style.display='none'" />`
              : `<span class="profile-avatar-fallback" style="width: 80px; height: 80px; border-radius: 50%; background: var(--accent); color: var(--bg); display: inline-flex; align-items: center; justify-content: center; font-size: 1.75rem; font-weight: 700; flex-shrink: 0;">${escapeHtml(initials)}</span>`
          }
          <div>
            <h3 style="margin: 0; font-size: 1.4rem;">${escapeHtml(displayName)}</h3>
            <p class="muted" style="margin: 0.25rem 0;">${escapeHtml(user.email)}</p>
            ${user.studentId ? `<p style="margin: 0.15rem 0; font-size: 0.9rem; color: var(--accent);"><strong>ID:</strong> ${escapeHtml(user.studentId)}</p>` : ""}
            <div class="status-pill solved" style="margin-top: 0.4rem;">Member since ${escapeHtml(user.createdAt ? new Date(user.createdAt).toLocaleDateString() : "today")}</div>
          </div>
        </article>

        <article class="card profile-stat">
          <h4>Total Solved</h4>
          <div class="big-number">${escapeHtml(user.totalProblemsSolved ?? 0)}</div>
        </article>
      </div>

      ${user.bio ? `
        <div class="card" style="margin-top: 1rem;">
          <h3>About</h3>
          <p style="margin: 0.5rem 0 0 0; line-height: 1.6;">${escapeHtml(user.bio)}</p>
        </div>
      ` : ""}

      <div class="card" style="margin-top: 1rem;">
        <h3>Student Details</h3>
        <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 1rem; margin-top: 0.75rem;">
          ${user.phone ? `<div><span class="muted">Phone</span><p style="margin: 0.25rem 0; font-weight: 500;">${escapeHtml(user.phone)}</p></div>` : ""}
          ${user.profession ? `<div><span class="muted">Profession</span><p style="margin: 0.25rem 0; font-weight: 500;">${escapeHtml(user.profession)}</p></div>` : ""}
          ${user.college ? `<div><span class="muted">College / University</span><p style="margin: 0.25rem 0; font-weight: 500;">${escapeHtml(user.college)}</p></div>` : ""}
          ${user.branch ? `<div><span class="muted">Branch</span><p style="margin: 0.25rem 0; font-weight: 500;">${escapeHtml(user.branch)}</p></div>` : ""}
          ${user.graduationYear ? `<div><span class="muted">Graduation Year</span><p style="margin: 0.25rem 0; font-weight: 500;">${escapeHtml(user.graduationYear)}</p></div>` : ""}
          ${user.location ? `<div><span class="muted">Location</span><p style="margin: 0.25rem 0; font-weight: 500;">${escapeHtml(user.location)}</p></div>` : ""}
          ${
            user.skills
              ? `<div style="grid-column: 1 / -1;"><span class="muted">Skills</span><div style="display: flex; flex-wrap: wrap; gap: 0.4rem; margin-top: 0.35rem;">${user.skills.split(",").map((skill) => `<span class="tag-chip">${escapeHtml(skill.trim())}</span>`).join("")}</div></div>`
              : ""
          }
          ${user.linkedin ? `<div style="min-width: 0;"><span class="muted">LinkedIn</span><p style="margin: 0.25rem 0;"><a href="${escapeHtml(user.linkedin)}" target="_blank" rel="noopener noreferrer" style="color: var(--accent); overflow-wrap: anywhere; word-break: break-word;">${escapeHtml(user.linkedin)}</a></p></div>` : ""}
          ${user.github ? `<div style="min-width: 0;"><span class="muted">GitHub</span><p style="margin: 0.25rem 0;"><a href="${escapeHtml(user.github)}" target="_blank" rel="noopener noreferrer" style="color: var(--accent); overflow-wrap: anywhere; word-break: break-word;">${escapeHtml(user.github)}</a></p></div>` : ""}
        </div>
      </div>

      <div class="card" style="margin-top: 1rem;">
        <h3>Language-wise Accepted Submissions</h3>
        <div class="language-stat-grid" style="margin-top: 0.75rem;">
          ${languageStats.length
            ? languageStats.map((item) => `
                <div class="language-stat">
                  <span class="lang-chip">${escapeHtml(item.language)}</span>
                  <strong>${escapeHtml(item.acceptedSubmissions)}</strong>
                </div>
              `).join("")
            : `<p class="muted">No accepted submissions yet. Start solving problems to see your stats!</p>`
          }
        </div>
      </div>
    </div>
  `;
}

function renderSubmissionsPage(submissions) {
  if (!state.user) {
    return pageMessageHtml("Please Login", "Please login through BUILD UP PILOT to view your submissions.");
  }

  const acceptedCount = submissions.filter((submission) => submission.verdict === "ACCEPTED").length;
  const averageRuntime = submissions.length
    ? Math.round(
        submissions.reduce((total, submission) => total + Number(submission.executionTimeMs || 0), 0) /
          submissions.length
      )
    : 0;

  return `
    <div class="page">
      <div class="hero">
        <h1>Submission History</h1>
        <p>Review verdicts, language performance, and runtime trends.</p>
      </div>

      <div class="journey-grid">
        <article class="card journey-card">
          <h3>Total Submissions</h3>
          <div class="big-number">${escapeHtml(submissions.length)}</div>
          <p class="muted">All runs and final submissions recorded in Skill Up.</p>
        </article>
        <article class="card journey-card">
          <h3>Accepted</h3>
          <div class="big-number">${escapeHtml(acceptedCount)}</div>
          <p class="muted">Successful outcomes across all attempted problems.</p>
        </article>
        <article class="card journey-card">
          <h3>Average Runtime</h3>
          <div class="big-number">${escapeHtml(averageRuntime)}</div>
          <p class="muted">Average execution time in milliseconds.</p>
        </article>
      </div>

      <div class="filters">
        <select id="submission-verdict">
          <option value="">All Verdicts</option>
          ${["ACCEPTED", "WRONG_ANSWER", "RUNTIME_ERROR", "COMPILATION_ERROR", "TIME_LIMIT_EXCEEDED", "INTERNAL_ERROR"]
            .map((verdict) => `<option value="${verdict}" ${state.submissionsFilters.verdict === verdict ? "selected" : ""}>${verdict}</option>`)
            .join("")}
        </select>
        <select id="submission-language">
          <option value="">All Languages</option>
          ${["C", "CPP", "PYTHON", "JAVA", "JAVASCRIPT", "HTML", "CSS"]
            .map((language) => `<option value="${language}" ${state.submissionsFilters.language === language ? "selected" : ""}>${language}</option>`)
            .join("")}
        </select>
      </div>

      <div class="card">
        <h3>Your Submissions</h3>
        ${
          submissions.length
            ? `
              <table class="table">
                <thead>
                  <tr>
                    <th>Problem</th>
                    <th>Verdict</th>
                    <th>Language</th>
                    <th>Mode</th>
                    <th>Exec(ms)</th>
                    <th>Time</th>
                  </tr>
                </thead>
                <tbody>
                  ${submissions
                    .map(
                      (submission) => `
                        <tr>
                          <td><a href="/problems/${encodeURIComponent(submission.problem.slug)}" data-link>${escapeHtml(submission.problem.title)}</a></td>
                          <td>${escapeHtml(submission.verdict)}</td>
                          <td>${escapeHtml(submission.language)}</td>
                          <td>${escapeHtml(submission.mode)}</td>
                          <td>${escapeHtml(submission.executionTimeMs)}</td>
                          <td>${escapeHtml(new Date(submission.createdAt).toLocaleString())}</td>
                        </tr>
                      `
                    )
                    .join("")}
                </tbody>
              </table>
            `
            : `<p class="muted">Your submission history will appear here once you start solving problems.</p>`
        }
      </div>
    </div>
  `;
}

function attachSubmissionFilters() {
  const update = () => {
    state.submissionsFilters.verdict = document.getElementById("submission-verdict")?.value || "";
    state.submissionsFilters.language = document.getElementById("submission-language")?.value || "";
    renderRoute();
  };

  const verdictSelect = document.getElementById("submission-verdict");
  const languageSelect = document.getElementById("submission-language");
  if (verdictSelect) verdictSelect.addEventListener("change", update);
  if (languageSelect) languageSelect.addEventListener("change", update);
}

function renderJourneysPage(journeys) {
  if (!state.user) {
    return pageMessageHtml("Please Login", "Please login through BUILD UP PILOT to view your learning journeys.");
  }

  const daysOnPortal = state.user?.createdAt
    ? Math.max(
        1,
        Math.ceil((Date.now() - new Date(state.user.createdAt).getTime()) / (1000 * 60 * 60 * 24))
      )
    : 0;
  const solvedProblems = Number(state.user?.totalProblemsSolved || 0);
  const totalJourneys = journeys.length;

  return `
    <div class="page">
      <div class="hero">
        <h1>Learning Journeys</h1>
        <p>Follow structured tracks and unlock consistent progress.</p>
      </div>

      <div class="journey-grid">
        <article class="card journey-card">
          <h3>Days on Skill Up</h3>
          <div class="big-number">${escapeHtml(daysOnPortal)}</div>
          <p class="muted">Time spent progressing since your Skill Up account was created.</p>
        </article>
        <article class="card journey-card">
          <h3>Problems Solved</h3>
          <div class="big-number">${escapeHtml(solvedProblems)}</div>
          <p class="muted">Accepted solutions tracked across all journeys.</p>
        </article>
        <article class="card journey-card">
          <h3>Active Journeys</h3>
          <div class="big-number">${escapeHtml(totalJourneys)}</div>
          <p class="muted">Structured learning tracks available to you right now.</p>
        </article>
      </div>

      <div class="journey-grid">
        ${
          journeys.length
            ? journeys
                .map(
                  (journey) => `
                    <article class="card journey-card">
                      <div class="journey-head">
                        <h3>${escapeHtml(journey.title)}</h3>
                        <span class="status-pill solved">${escapeHtml(journey.progressPercent)}%</span>
                      </div>
                      <p class="muted">${escapeHtml(journey.description)}</p>
                      <p>${escapeHtml(journey.solvedProblems)}/${escapeHtml(journey.totalProblems)} solved</p>
                      <div class="progress">
                        <div class="progress-fill" style="width:${escapeHtml(journey.progressPercent)}%;"></div>
                      </div>
                      <div class="journey-problems">
                        ${journey.problems
                          .map(
                            (problem) => `
                              <div class="journey-problem-row">
                                <span>${escapeHtml(problem.orderIndex)}. ${escapeHtml(problem.title)}</span>
                                <span class="status-pill ${problem.solved ? "solved" : "pending"}">${problem.solved ? "Solved" : "Pending"}</span>
                              </div>
                            `
                          )
                          .join("")}
                      </div>
                    </article>
                  `
                )
                .join("")
            : `<article class="card"><h3>No journeys assigned yet</h3><p class="muted">Your learning tracks will appear here once they are available in Skill Up.</p></article>`
        }
      </div>
    </div>
  `;
}

async function renderRoute() {
  state.route = parseRoute();
  const route = state.route;

  switch (route.name) {
    case "problems": {
      renderApp(pageLoadingHtml("Daily Coding Practice", "Loading problems..."));
      try {
        const data = await api("/problems", { query: state.problemFilters });
        if (state.route.name !== route.name) return;
        renderApp(renderProblemsPage(data.problems || data || []));
        attachProblemFilters();
      } catch {
        renderApp(pageMessageHtml("Problems Unavailable", "Unable to load problems right now."));
      }
      return;
    }

    case "problem-detail": {
      renderApp(pageLoadingHtml("Problem Workspace", "Loading challenge..."));
      try {
        const data = await api(`/problems/${encodeURIComponent(route.slug)}`);
        const problem = data.problem;
        if (!problem) {
          renderApp(pageMessageHtml("Problem not found", "The problem you are looking for does not exist."));
          return;
        }

        if (!(problem.supportedLanguages || []).includes(state.problemDetail.language)) {
          state.problemDetail.language = problem.supportedLanguages?.[0] || "PYTHON";
        }

        if (state.problemDetail.problemSlug !== route.slug) {
          state.problemDetail.problemSlug = route.slug;
          state.problemDetail.result = null;
          state.problemDetail.execError = null;
          state.problemDetail.sourceCode =
            problem.starterCodes?.[state.problemDetail.language] || "# Write your solution\n";
        }

        renderApp(renderProblemDetailPage(problem, data.submissions || []));
        ensureEditor(problem);
      } catch {
        renderApp(pageMessageHtml("Problem not found", "Unable to load this problem right now."));
      }
      return;
    }

    case "profile": {
      renderApp(pageLoadingHtml("Profile Snapshot", "Loading your profile..."));
      await enrichUserProfile();
      renderApp(renderProfilePage(state.user));
      return;
    }

    case "submissions": {
      renderApp(pageLoadingHtml("Submission History", "Loading your submissions..."));
      if (!state.user) {
        renderApp(renderSubmissionsPage([]));
        return;
      }
      try {
        const data = await api("/submissions/me", { query: state.submissionsFilters });
        renderApp(renderSubmissionsPage(data.submissions || []));
        attachSubmissionFilters();
      } catch {
        renderApp(pageMessageHtml("Submissions Unavailable", "Unable to load your submissions right now."));
      }
      return;
    }

    case "journeys": {
      renderApp(pageLoadingHtml("Learning Journeys", "Loading your tracks..."));
      if (!state.user) {
        renderApp(renderJourneysPage([]));
        return;
      }
      try {
        const data = await api("/journeys");
        renderApp(renderJourneysPage(data.journeys || []));
      } catch {
        renderApp(pageMessageHtml("Journeys Unavailable", "Unable to load your learning journeys right now."));
      }
      return;
    }

    default:
      navigate("/problems", true);
  }
}

window.addEventListener("popstate", () => {
  renderRoute();
});

document.addEventListener("click", (event) => {
  const anchor = event.target.closest("a");
  if (!anchor) return;
  const href = anchor.getAttribute("href");
  if (!href || anchor.target === "_blank" || href.startsWith("http")) return;
  if (anchor.hasAttribute("data-link")) {
    event.preventDefault();
    navigate(href);
  }
});

async function boot() {
  applyTheme();
  renderApp(pageLoadingHtml("SKILL UP", "Preparing your workspace..."));
  state.route = parseRoute();
  await initAuth();
  await renderRoute();
}

boot();
