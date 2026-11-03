import { createContext, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";

import { authApi, setAccessToken, type User } from "../services/api";

type AuthContextValue = {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    authApi.me().then(({ data }) => setUser(data)).catch(() => undefined).finally(() => setLoading(false));
  }, []);

  const value = useMemo<AuthContextValue>(() => ({
    user,
    loading,
    login: async (email, password) => {
      const { data } = await authApi.login(email, password);
      setAccessToken(data.access_token);
      setUser((await authApi.me()).data);
    },
    register: async (name, email, password) => {
      const { data } = await authApi.register(name, email, password);
      setAccessToken(data.access_token);
      setUser((await authApi.me()).data);
    },
    logout: async () => {
      await authApi.logout().catch(() => undefined);
      setAccessToken(null);
      setUser(null);
    },
  }), [loading, user]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
}
