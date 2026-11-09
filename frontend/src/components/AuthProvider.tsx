
"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  ReactNode,
} from "react";
import { usePathname, useRouter } from "next/navigation";
import api, { clearAuthToken, getAuthToken } from "@/lib/api";

export interface AuthUser {
  id: number;
  full_name: string;
  email: string;
  role: "admin" | "health_worker" | "supervisor" | "doctor";
  is_active: boolean;
}

interface AuthContextType {
  user: AuthUser | null;
  loading: boolean;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const ROLE_HOME: Record<AuthUser["role"], string> = {
  admin: "/",
  health_worker: "/intake",
  supervisor: "/supervisor",
  doctor: "/doctor",
};

const ROLE_ROUTES: Record<AuthUser["role"], string[]> = {
  admin: ["/"],
  health_worker: ["/intake"],
  supervisor: ["/", "/supervisor", "/analytics"],
  doctor: ["/", "/doctor"],
};

function canAccessRoute(role: AuthUser["role"], pathname: string) {
  if (role === "admin") return true;

  return ROLE_ROUTES[role].some((route) => {
    if (route === "/") return pathname === "/";
    return pathname === route || pathname.startsWith(`${route}/`);
  });
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();

  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  const isLoginPage = pathname === "/login";

  useEffect(() => {
    let active = true;

    async function verifyAuthentication() {
      if (isLoginPage) {
        setLoading(false);
        return;
      }

      const token = getAuthToken();

      if (!token) {
        setUser(null);
        setLoading(false);
        router.replace("/login");
        return;
      }

      setLoading(true);

      try {
        const response = await api.get<AuthUser>("/auth/me");
        const authenticatedUser = response.data;

        if (!authenticatedUser.is_active) {
          throw new Error("Account is inactive.");
        }

        if (!active) return;

        setUser(authenticatedUser);

        if (!canAccessRoute(authenticatedUser.role, pathname)) {
          router.replace(ROLE_HOME[authenticatedUser.role]);
        }
      } catch {
        if (!active) return;

        clearAuthToken();
        sessionStorage.removeItem("smarttriage_user");
        setUser(null);
        router.replace("/login");
      } finally {
        if (active) setLoading(false);
      }
    }

    verifyAuthentication();

    return () => {
      active = false;
    };
  }, [pathname, router, isLoginPage]);

  const logout = () => {
    clearAuthToken();
    sessionStorage.removeItem("smarttriage_user");
    setUser(null);
    router.replace("/login");
  };

  if (isLoginPage) {
    return (
      <AuthContext.Provider value={{ user, loading, logout }}>
        {children}
      </AuthContext.Provider>
    );
  }

  if (loading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-center">
          <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-teal-600" />
          <p className="mt-4 text-sm text-slate-500">
            Verifying your access...
          </p>
        </div>
      </div>
    );
  }

  return (
    <AuthContext.Provider value={{ user, loading, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider.");
  }

  return context;
}
