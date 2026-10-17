import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { getSession, loginAccount, logoutAccount } from "../services/account.ts";
import { onSessionLost } from "../services/session.ts";
import type { PublicUser } from "../types/account.ts";

type AuthStatus = "loading" | "ready";

interface AuthValue {
  status: AuthStatus;
  user: PublicUser | null;
  refresh: () => Promise<void>;
  login: (email: string, password: string) => Promise<PublicUser>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [user, setUser] = useState<PublicUser | null>(null);

  const refresh = useCallback(async () => {
    const session = await getSession();
    setUser(session.authenticated ? session.user : null);
    setStatus("ready");
  }, []);

  useEffect(() => onSessionLost(() => {
    setUser(null);
    setStatus("ready");
  }), []);

  useEffect(() => {
    let cancelled = false;
    getSession()
      .then((session) => {
        if (!cancelled) {
          setUser(session.authenticated ? session.user : null);
          setStatus("ready");
        }
      })
      .catch(() => {
        if (!cancelled) {
          setUser(null);
          setStatus("ready");
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const session = await loginAccount(email, password);
    const next = session.user;
    if (!next) {
      throw new Error("Sign-in did not return an account.");
    }
    setUser(next);
    setStatus("ready");
    return next;
  }, []);

  const logout = useCallback(async () => {
    await logoutAccount();
    setUser(null);
    setStatus("ready");
  }, []);

  const value = useMemo(
    () => ({ status, user, refresh, login, logout }),
    [status, user, refresh, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthValue {
  const value = useContext(AuthContext);
  if (!value) {
    throw new Error("useAuth must be used inside AuthProvider.");
  }
  return value;
}
