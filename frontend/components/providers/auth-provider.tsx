"use client";

import * as React from "react";
import { User, UserRole, LoginRequest, loginUser, logoutUser, getCurrentUser } from "@/lib/api/auth";

interface AuthContextType {
  user: User | null;
  role: UserRole | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginRequest) => Promise<User>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = React.createContext<AuthContextType | undefined>(undefined);

const STORAGE_KEY = "gtp-auth-user";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = React.useState<User | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);

  // Initialize from localStorage snapshot if available
  React.useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        setUser(JSON.parse(stored));
      }
    } catch {
      // ignore JSON parse errors
    }

    // Then verify with the live backend Flask session
    refreshUser().finally(() => {
      setIsLoading(false);
    });
  }, []);

  const refreshUser = async () => {
    try {
      const res = await getCurrentUser();
      if (res.authenticated && res.user) {
        setUser(res.user);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(res.user));
      } else {
        // If not authenticated in Flask session, keep or clear
        // Only clear if active check completed and confirmed no session
        setUser(null);
        localStorage.removeItem(STORAGE_KEY);
      }
    } catch {
      // Backend may be booting or offline; keep cached if any
    }
  };

  const login = async (credentials: LoginRequest): Promise<User> => {
    setIsLoading(true);
    try {
      const res = await loginUser(credentials);
      if (res.success && res.user) {
        setUser(res.user);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(res.user));
        return res.user;
      }
      throw new Error(res.error || "Login failed");
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      await logoutUser();
    } catch {
      // proceed with client logout regardless
    }
    setUser(null);
    localStorage.removeItem(STORAGE_KEY);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        role: user?.role ?? null,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
