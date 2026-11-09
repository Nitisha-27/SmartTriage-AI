
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";
import api, { setAuthToken } from "@/lib/api";
import {
  Activity,
  ShieldCheck,
  LockKeyhole,
  Mail,
  Eye,
  EyeOff,
  Loader2,
} from "lucide-react";

interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: {
    id: number;
    full_name: string;
    email: string;
    role: string;
    is_active: boolean;
  };
}

export default function LoginPage() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleLogin = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      const formData = new URLSearchParams();
      formData.append("username", email);
      formData.append("password", password);

      const response = await api.post<LoginResponse>(
        "/auth/login",
        formData,
        {
          headers: {
            "Content-Type": "application/x-www-form-urlencoded",
          },
        }
      );

      const data = response.data;

      if (!data.access_token || !data.user) {
        throw new Error("Invalid login response from server.");
      }

      setAuthToken(data.access_token);

      // Fetch the authenticated user's profile
      const profileResponse = await api.get("/auth/me");
      const user = profileResponse.data;

      // Save non-sensitive profile information for the UI
      sessionStorage.setItem(
        "smarttriage_user",
        JSON.stringify(user)
      );

      // Redirect according to role
      switch (user.role) {
        case "admin":
          router.push("/");
          break;

        case "health_worker":
          router.push("/intake");
          break;

        case "supervisor":
          router.push("/supervisor");
          break;

        case "doctor":
          router.push("/doctor");
          break;

        default:
          setError("Your account does not have a recognized role.");
          sessionStorage.removeItem("smarttriage_access_token");
          sessionStorage.removeItem("smarttriage_user");
      }
    } catch (err: unknown) {
  console.error("Login error:", err);

  if (axios.isAxiosError<{ detail?: string }>(err)) {
    if (err.response?.status === 401) {
      setError("Incorrect email or password.");
    } else if (err.response?.status === 403) {
      setError("Your account is inactive or access is restricted.");
    } else {
      setError(
        err.response?.data?.detail ||
        "Unable to connect to the server. Please try again."
      );
    }
  } else {
    setError(
      err instanceof Error
        ? err.message
        : "Something went wrong. Please try again."
    );
  }
}
  };

  return (
    <main className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <div className="w-full max-w-5xl grid grid-cols-1 md:grid-cols-2 bg-white rounded-2xl shadow-xl overflow-hidden">

        {/* Left branding section */}
        <div className="hidden md:flex flex-col justify-between bg-slate-900 text-white p-10">
          <div>
            <div className="flex items-center gap-3">
              <div className="bg-teal-500 p-2 rounded-xl">
                <Activity size={26} />
              </div>
              <div>
                <h1 className="text-2xl font-bold">SmartTriage AI</h1>
                <p className="text-xs text-slate-300">
                  Intelligent Clinical Triage Platform
                </p>
              </div>
            </div>

            <div className="mt-20">
              <h2 className="text-3xl font-bold leading-tight">
                Smarter triage.
                <br />
                Structured decisions.
                <br />
                Better coordination.
              </h2>

              <p className="text-slate-300 mt-5 leading-7">
                A role-based clinical triage and referral platform
                designed to support healthcare workflows through
                AI-assisted risk assessment and human review.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 text-sm text-slate-300">
            <ShieldCheck size={18} className="text-teal-400" />
            Secure role-based access
          </div>
        </div>

        {/* Login form */}
        <div className="p-7 sm:p-10 md:p-12 flex flex-col justify-center">
          <div className="md:hidden flex items-center gap-3 mb-10">
            <div className="bg-teal-600 text-white p-2 rounded-xl">
              <Activity size={24} />
            </div>
            <h1 className="text-xl font-bold text-slate-900">
              SmartTriage AI
            </h1>
          </div>

          <div className="mb-8">
            <p className="text-sm font-semibold text-teal-700 mb-2">
              WELCOME BACK
            </p>

            <h2 className="text-3xl font-bold text-slate-900">
              Sign in to your account
            </h2>

            <p className="text-slate-500 mt-2 text-sm">
              Enter your credentials to access your workspace.
            </p>
          </div>

          <form onSubmit={handleLogin} className="space-y-5">
            <div>
              <label
                htmlFor="email"
                className="block text-sm font-medium text-slate-700 mb-2"
              >
                Email address
              </label>

              <div className="relative">
                <Mail
                  size={18}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
                />

                <input
                  id="email"
                  type="email"
                  required
                  autoComplete="username"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Enter your email"
                  className="w-full border border-slate-300 rounded-lg pl-10 pr-4 py-3 text-sm text-slate-900 outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
                />
              </div>
            </div>

            <div>
              <label
                htmlFor="password"
                className="block text-sm font-medium text-slate-700 mb-2"
              >
                Password
              </label>

              <div className="relative">
                <LockKeyhole
                  size={18}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
                />

                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  required
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  className="w-full border border-slate-300 rounded-lg pl-10 pr-12 py-3 text-sm text-slate-900 outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
                />

                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-700"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            {error && (
              <div
                role="alert"
                className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-3 text-sm"
              >
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-teal-600 hover:bg-teal-700 disabled:opacity-60 disabled:cursor-not-allowed text-white font-semibold rounded-lg py-3 flex items-center justify-center gap-2 transition-colors"
            >
              {loading ? (
                <>
                  <Loader2 size={18} className="animate-spin" />
                  Signing in...
                </>
              ) : (
                "Sign in"
              )}
            </button>
          </form>

          <div className="mt-8 border-t border-slate-200 pt-5">
            <p className="text-xs text-slate-500 text-center leading-5">
              Authorized personnel only. Access is controlled by your
              assigned user role.
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
