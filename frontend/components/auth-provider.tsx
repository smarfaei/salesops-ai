"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { api, setAccessToken } from "@/lib/api";
import { hasPermission, type Permission } from "@/lib/permissions";
import type { User } from "@/types";

type AuthContextValue = {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  can: (permission: Permission) => boolean;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    void api
      .refresh()
      .then((session) => {
        if (active) setUser(session.user);
      })
      .catch(() => {
        setAccessToken(null);
        if (active) setUser(null);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      loading,
      login: async (email, password) => {
        const session = await api.login(email, password);
        setUser(session.user);
      },
      logout: async () => {
        await api.logout();
        setUser(null);
      },
      can: (permission) =>
        Boolean(user && hasPermission(user.role, permission)),
    }),
    [user, loading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
}
