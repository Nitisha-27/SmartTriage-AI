
"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Users,
  ClipboardList,
  CheckCircle,
  AlertTriangle,
  RefreshCw,
  Stethoscope,
} from "lucide-react";

import api from "@/lib/api";
import { useAuth } from "@/components/AuthProvider";
import Sidebar from "@/components/Sidebar";
import Header from "@/components/Header";
import StatCard from "@/components/StatCard";
import TriageChart from "@/components/TriageChart";
import RecentCases from "@/components/RecentCases";

interface Summary {
  total_cases: number;
  pending_reviews: number;
  approved_for_doctor: number;
  completed_cases: number;
  total_reviewed_cases: number;
}

interface Distribution {
  ai_distribution: {
    total_predictions: number;
    counts: Record<string, number>;
    percentages: Record<string, number>;
  };
  supervisor_distribution: {
    total_verified_cases: number;
    counts: Record<string, number>;
    percentages: Record<string, number>;
  };
}

interface Discordance {
  total_reviewed_cases_with_ai_prediction: number;
  total_discordant_cases: number;
  total_agreement_cases: number;
  discordance_rate_percent: number;
  agreement_rate_percent: number;
}

interface PatientCase {
  id?: number;
  case_id: number;
  patient_name: string;
  age: number;
  gender: string;
  ai_triage_tier: string | null;
  human_verified_tier: string | null;
  syndrome_match: string | null;
  status: string;
  created_at: string;
}

function extractCases(data: unknown): PatientCase[] {
  if (Array.isArray(data)) {
    return data as PatientCase[];
  }

  if (data && typeof data === "object") {
    const result = data as Record<string, unknown>;

    if (Array.isArray(result.cases)) {
      return result.cases as PatientCase[];
    }

    if (Array.isArray(result.pending_cases)) {
      return result.pending_cases as PatientCase[];
    }
  }

  return [];
}

export default function Dashboard() {
  const { user } = useAuth();

  const [summary, setSummary] = useState<Summary | null>(null);
  const [distribution, setDistribution] =
    useState<Distribution | null>(null);
  const [discordance, setDiscordance] =
    useState<Discordance | null>(null);

  const [cases, setCases] = useState<PatientCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const role = user?.role;

  const fetchDashboardData = useCallback(async () => {
    if (!role) return;

    setLoading(true);
    setError("");

    setSummary(null);
    setDistribution(null);
    setDiscordance(null);
    setCases([]);

    const requests: Promise<void>[] = [];

    // ADMIN AND SUPERVISOR: Analytics access
    if (role === "admin" || role === "supervisor") {
      requests.push(
        api.get("/analytics/summary")
          .then((response) => setSummary(response.data))
      );

      requests.push(
        api.get("/analytics/triage-distribution")
          .then((response) => setDistribution(response.data))
      );

      requests.push(
        api.get("/analytics/discordance")
          .then((response) => setDiscordance(response.data))
      );
    }

    // ADMIN AND DOCTOR: Doctor queue access
    if (role === "admin" || role === "doctor") {
      requests.push(
        api.get("/cases/queue")
          .then((response) => {
            setCases(extractCases(response.data));
          })
      );
    }

    // SUPERVISOR: Pending cases access
    if (role === "supervisor") {
      requests.push(
        api.get("/cases/pending")
          .then((response) => {
            setCases(extractCases(response.data));
          })
      );
    }

    const results = await Promise.allSettled(requests);

    const failedRequests = results.filter(
      (result) => result.status === "rejected"
    );

    if (failedRequests.length > 0) {
      console.error("Some dashboard requests failed:", failedRequests);
      setError(
        "Some dashboard information could not be loaded. Please refresh."
      );
    }

    setLoading(false);
  }, [role]);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  const isAnalyticsRole =
    role === "admin" || role === "supervisor";

  const isDoctor = role === "doctor";

  const dashboardTitle =
    role === "doctor"
      ? "Doctor Dashboard"
      : role === "supervisor"
      ? "Supervisor Dashboard"
      : "Dashboard Overview";

  const dashboardDescription =
    role === "doctor"
      ? "Monitor your consultation queue and assigned patient cases."
      : role === "supervisor"
      ? "Monitor patient assessments and AI-supervisor decisions."
      : "Real-time overview of the SmartTriage workflow.";

  return (
    <div className="min-h-screen bg-slate-50">
      <Sidebar />

      <main className="ml-64 min-h-screen">
        <Header />

        <div className="space-y-8 p-8">

          {/* Dashboard heading */}
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-slate-800">
                {dashboardTitle}
              </h1>

              <p className="mt-1 text-sm text-slate-500">
                {dashboardDescription}
              </p>
            </div>

            <button
              onClick={fetchDashboardData}
              disabled={loading}
              className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 shadow-sm hover:bg-slate-50 disabled:opacity-50"
            >
              <RefreshCw
                size={16}
                className={loading ? "animate-spin" : ""}
              />
              Refresh
            </button>
          </div>

          {/* Error message */}
          {error && (
            <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-700">
              {error}
            </div>
          )}

          {loading ? (
            <div className="rounded-xl border border-slate-200 bg-white p-12 text-center text-slate-500">
              Loading dashboard data...
            </div>
          ) : (
            <>

              {/* DOCTOR DASHBOARD */}
              {isDoctor && (
                <>
                  <section className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
                    <StatCard
                      title="Doctor Queue"
                      value={cases.length}
                      subtitle="Cases available for consultation"
                      icon={Stethoscope}
                      iconColor="text-blue-600"
                      iconBackground="bg-blue-50"
                    />

                    <StatCard
                      title="Emergent Cases"
                      value={
                        cases.filter(
                          (item) =>
                            item.ai_triage_tier === "Emergent" ||
                            item.human_verified_tier === "Emergent"
                        ).length
                      }
                      subtitle="Cases marked emergent"
                      icon={AlertTriangle}
                      iconColor="text-red-600"
                      iconBackground="bg-red-50"
                    />

                    <StatCard
                      title="Available Cases"
                      value={cases.length}
                      subtitle="Awaiting doctor consultation"
                      icon={ClipboardList}
                      iconColor="text-emerald-600"
                      iconBackground="bg-emerald-50"
                    />
                  </section>

                  <RecentCases cases={cases} />
                </>
              )}

              {/* SUPERVISOR AND ADMIN ANALYTICS */}
              {isAnalyticsRole && (
                <>
                  <section className="grid gap-5 sm:grid-cols-2 xl:grid-cols-4">

                    <StatCard
                      title="Total Cases"
                      value={summary?.total_cases ?? "—"}
                      subtitle="All submitted patient cases"
                      icon={Users}
                      iconColor="text-blue-600"
                      iconBackground="bg-blue-50"
                    />

                    <StatCard
                      title="Pending Reviews"
                      value={summary?.pending_reviews ?? "—"}
                      subtitle="Awaiting supervisor review"
                      icon={ClipboardList}
                      iconColor="text-amber-600"
                      iconBackground="bg-amber-50"
                    />

                    <StatCard
                      title="Completed Cases"
                      value={summary?.completed_cases ?? "—"}
                      subtitle="Doctor consultations completed"
                      icon={CheckCircle}
                      iconColor="text-emerald-600"
                      iconBackground="bg-emerald-50"
                    />

                    <StatCard
                      title="Discordance Rate"
                      value={
                        discordance
                          ? `${discordance.discordance_rate_percent}%`
                          : "—"
                      }
                      subtitle={
                        discordance
                          ? `${discordance.total_discordant_cases} differing decisions`
                          : "AI-supervisor comparison"
                      }
                      icon={AlertTriangle}
                      iconColor="text-purple-600"
                      iconBackground="bg-purple-50"
                    />
                  </section>

                  <section className="grid gap-6 xl:grid-cols-3">
                    <div className="xl:col-span-2">
                      {distribution ? (
                        <TriageChart
                          aiCounts={distribution.ai_distribution.counts}
                          supervisorCounts={
                            distribution.supervisor_distribution.counts
                          }
                        />
                      ) : (
                        <div className="rounded-xl border bg-white p-8 text-slate-500">
                          Triage distribution unavailable.
                        </div>
                      )}
                    </div>

                    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
                      <h3 className="text-lg font-semibold text-slate-800">
                        Review Agreement
                      </h3>

                      <p className="mt-1 text-sm text-slate-500">
                        AI and supervisor tier comparison
                      </p>

                      <div className="mt-8 flex flex-col items-center">
                        <div className="flex h-36 w-36 flex-col items-center justify-center rounded-full border-[10px] border-emerald-100">
                          <span className="text-3xl font-bold text-slate-800">
                            {discordance?.agreement_rate_percent ?? 0}%
                          </span>

                          <span className="text-xs text-slate-500">
                            Agreement
                          </span>
                        </div>

                        <div className="mt-7 w-full space-y-4">
                          <div className="flex justify-between text-sm">
                            <span className="text-slate-500">
                              Agreement cases
                            </span>

                            <span className="font-semibold text-emerald-600">
                              {discordance?.total_agreement_cases ?? 0}
                            </span>
                          </div>

                          <div className="flex justify-between text-sm">
                            <span className="text-slate-500">
                              Discordant cases
                            </span>

                            <span className="font-semibold text-red-600">
                              {discordance?.total_discordant_cases ?? 0}
                            </span>
                          </div>

                          <div className="flex justify-between text-sm">
                            <span className="text-slate-500">
                              Reviewed with AI prediction
                            </span>

                            <span className="font-semibold text-slate-800">
                              {discordance?.total_reviewed_cases_with_ai_prediction ?? 0}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </section>

                  {role === "supervisor" && (
                    <RecentCases cases={cases} />
                  )}
                </>
              )}

              <footer className="pb-4 text-center text-xs text-slate-400">
                SmartTriage AI · Educational prototype · Not clinically validated
              </footer>

            </>
          )}
        </div>
      </main>
    </div>
  );
}
