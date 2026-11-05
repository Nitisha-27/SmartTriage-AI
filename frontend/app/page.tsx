
"use client";

import { useEffect, useState } from "react";
import {
  Users,
  ClipboardList,
  CheckCircle,
  AlertTriangle,
  RefreshCw,
} from "lucide-react";

import api from "@/lib/api";
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

export default function Dashboard() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [distribution, setDistribution] = useState<Distribution | null>(null);
  const [discordance, setDiscordance] = useState<Discordance | null>(null);
  const [cases, setCases] = useState<PatientCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchDashboardData = async () => {
    setLoading(true);
    setError("");

    try {
      const [
        summaryResponse,
        distributionResponse,
        discordanceResponse,
        queueResponse,
      ] = await Promise.all([
        api.get("/analytics/summary"),
        api.get("/analytics/triage-distribution"),
        api.get("/analytics/discordance"),
        api.get("/cases/queue"),
      ]);

      setSummary(summaryResponse.data);
      setDistribution(distributionResponse.data);
      setDiscordance(discordanceResponse.data);
      setCases(queueResponse.data.cases || []);
    } catch (err) {
      console.error("Dashboard loading error:", err);
      setError(
        "Unable to load dashboard data. Check that the FastAPI backend is running."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  return (
    <div className="min-h-screen bg-slate-50">
      <Sidebar />

      <main className="ml-64 min-h-screen">
        <Header />

        <div className="space-y-8 p-8">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-slate-800">
                Dashboard Overview
              </h1>
              <p className="mt-1 text-sm text-slate-500">
                Real-time overview of the SmartTriage workflow.
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

          {error && (
            <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              {error}
            </div>
          )}

          {loading && !summary ? (
            <div className="rounded-xl border border-slate-200 bg-white p-12 text-center text-slate-500">
              Loading dashboard data...
            </div>
          ) : (
            <>
              <section className="grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
                <StatCard
                  title="Total Cases"
                  value={summary?.total_cases ?? 0}
                  subtitle="All submitted patient cases"
                  icon={Users}
                  iconColor="text-blue-600"
                  iconBackground="bg-blue-50"
                />

                <StatCard
                  title="Pending Reviews"
                  value={summary?.pending_reviews ?? 0}
                  subtitle="Awaiting supervisor review"
                  icon={ClipboardList}
                  iconColor="text-amber-600"
                  iconBackground="bg-amber-50"
                />

                <StatCard
                  title="Completed Cases"
                  value={summary?.completed_cases ?? 0}
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

              <RecentCases cases={cases} />

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
