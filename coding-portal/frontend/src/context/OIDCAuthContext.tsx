import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import { User } from "../types";

interface OIDCAuthState {
  user: User | null;
  loading: boolean;
  oidcError: string | null;
  login: (email?: string, phone?: string) => Promise<void>;
  signup: (email: string, phone?: string) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
}

const OIDCAuthContext = createContext<OIDCAuthState | undefined>(undefined);

export function OIDCAuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [oidcError, setOidcError] = useState<string | null>(null);

  const refresh = async () => {
    try {
      const { data } = await api.get("/auth/me");
      setUser(data.user);
    } catch (error: any) {
      if (error.response?.status === 401) {
        setUser(null);
      }
    } finally {
      setLoading(false);
    }
  };

  const login = async (email?: string, phone?: string) => {
    try {
      const payload = email ? { email } : phone ? { phone } : { email: "demo@example.com" };
      const { data } = await api.post("/auth/login", payload);
      setUser(data.user);
      setOidcError(null);
    } catch (err: any) {
      console.error("Login failed:", err);
      setOidcError("Login failed. Please try again.");
    }
  };

  const signup = async (email: string, phone?: string) => {
    try {
      const payload = { email, ...(phone && { phone }) };
      const { data } = await api.post("/auth/signup", payload);
      setUser(data.user);
      setOidcError(null);
    } catch (err: any) {
      console.error("Signup failed:", err);
      setOidcError("Signup failed. Please try again.");
    }
  };

  useEffect(() => {
    const BUILDUP_BASE_URL =
      window.location.port === "5173" || window.location.port === "5174"
        ? `${window.location.protocol}//${window.location.hostname}:5002`
        : window.location.origin;

    const fetchBuildUpSsoToken = async () => {
      const response = await fetch(`${BUILDUP_BASE_URL}/api/skillup/sso-token`, {
        method: "GET",
        credentials: "include",
        headers: { Accept: "application/json" }
      });
      if (!response.ok) {
        throw new Error(`Build Up SSO bootstrap failed with status ${response.status}`);
      }
      return response.json();
    };

    const handleTokenFromURL = async () => {
      // Check for SSO token in URL parameters (from Build Up Pilot)
      const urlParams = new URLSearchParams(window.location.search);
      const ssoToken = urlParams.get("sso");

      if (ssoToken) {
        // Clean the URL immediately (remove sso param) so refresh won't retry
        const cleanUrl = window.location.origin + window.location.pathname;
        window.history.replaceState({}, "", cleanUrl);

        try {
          // Exchange SSO token for a session
          const { data } = await api.post("/auth/sso", { token: ssoToken });
          setUser(data.user);
          setOidcError(null);
          setLoading(false);
          return;
        } catch (err: any) {
          console.error("SSO token exchange failed, checking existing session...", err);
          // Don't show error yet — try existing session first
        }
      }

      // Regular authentication check (existing session or after failed SSO)
      try {
        const { data } = await api.get("/auth/me");
        setUser(data.user);
        setOidcError(null);
      } catch (error: any) {
        if (error.response?.status === 401) {
          // No coding-portal session — try to bootstrap from Build Up Pilot session
          try {
            const bootstrap = await fetchBuildUpSsoToken();
            if (bootstrap?.token) {
              const { data } = await api.post("/auth/sso", { token: bootstrap.token });
              setUser(data.user);
              setOidcError(null);
            } else {
              setUser(null);
            }
          } catch {
            // Build Up session is not available; keep Skill Up logged out
            setUser(null);
          }
        } else {
          setUser(null);
          if (ssoToken) {
            setOidcError("SSO login failed. Please try again from Build Up Pilot.");
          }
        }
      } finally {
        setLoading(false);
      }
    };

    handleTokenFromURL();
  }, []);

  const value = useMemo<OIDCAuthState>(
    () => ({
      user,
      loading,
      oidcError,
      login,
      signup,
      logout: async () => {
        try {
          await api.post("/auth/logout");
        } catch {
          // ignore
        }
        setUser(null);
      },
      refresh
    }),
    [user, loading]
  );

  return <OIDCAuthContext.Provider value={value}>{children}</OIDCAuthContext.Provider>;
}

export function useOIDCAuth() {
  const context = useContext(OIDCAuthContext);
  if (context === undefined) {
    throw new Error("useOIDCAuth must be used within OIDCAuthProvider");
  }
  return context;
}
