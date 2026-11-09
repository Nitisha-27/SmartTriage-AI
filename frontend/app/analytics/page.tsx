 "use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertCircle,
  CheckCircle,
  Clock,
  RefreshCw,
  ShieldCheck,
  TrendingUp,
  Users,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import api from "@/lib/api";
import Sidebar from "@/components/Sidebar";
import Header from "@/components/Header";

type Tier = "Routine" | "Urgent" | "Emergent";

interface SummaryData {
  total_cases: number;
  pending_reviews: number;
  approved_for_doctor: number;
  completed_cases: number;
  total_reviewed_cases: number;
}

interface DiscordanceData {
  total_reviewed_cases_with_ai_prediction: number;
  total_discordant_cases: number;
  total_agreement_cases: number;
  discordance_rate_percent: number;
  agreement_rate_percent: number;
  discordant_case_ids: number[];
  interpretation: string;
}

interface DistributionGroup {
  total_predictions?: number;
  total_verified_cases?: number;
  counts: Record<Tier, number>;
  percentages: Record<Tier, number>;
}

interface DistributionData {
  ai_distribution: DistributionGroup;
  supervisor_distribution: DistributionGroup;
}

const TIERS: Tier[] = ["Routine", "Urgent", "Emergent"];
const TIER_COLORS: Record<Tier, string> = {
  Routine: "#10b981",
  Urgent: "#f59e0b",
  Emergent: "#ef4444",
};

function formatNumber(value: number | undefined) {
  return typeof value === "number" ? value.toLocaleString() : "—";
}

function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
}: {
  title: string;
  value: string;
  subtitle: string;
  icon: React.ElementType;
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-slate-500">{title}</p>
          <p className="mt-2 text-3xl font-bold tracking-tight text-slate-800">
            {value}
          </p>
          <p className="mt-1 text-xs text-slate-400">{subtitle}</p>
        </div>
        <div className="rounded-lg bg-blue-50 p-3 text-blue-600">
          <Icon size={21} />
        </div>
      </div>
    </div>
  );
}

function EmptyChart({ message }: { message: string }) {
  return (
    <div className="flex h-64 items-center justify-center rounded-lg bg-slate-50 px-5 text-center text-sm text-slate-500">
      {message}
    </div>
  );
}

export default function AnalyticsPage() {
  const [summary, setSummary] = useState<SummaryData | null>(null);
  const [discordance, setDiscordance] = useState<DiscordanceData | null>(null);
  const [distribution, setDistribution] = useState<DistributionData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchAnalytics = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const [summaryResponse, discordanceResponse, distributionResponse] =
        await Promise.all([
          api.get("/analytics/summary"),
          api.get("/analytics/discordance"),
          api.get("/analytics/triage-distribution"),
        ]);

      setSummary(summaryResponse.data);
      setDiscordance(discordanceResponse.data);
      setDistribution(distributionResponse.data);
    } catch (err: any) {
      console.error("Analytics loading error:", err);
      setError(
        err?.response?.data?.detail ||
          "Unable to load analytics. Check your access permissions and backend connection."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  const comparisonData = useMemo(() => {
    if (!distribution) return [];
    return TIERS.map((tier) => ({
      tier,
      "AI predictions": distribution.ai_distribution.counts?.[tier] ?? 0,
      "Supervisor verified":
        distribution.supervisor_distribution.counts?.[tier] ?? 0,
    }));
  }, [distribution]);

  const aiPieData = useMemo(() => {
    if (!distribution) return [];
    return TIERS.map((tier) => ({
      name: tier,
      value: distribution.ai_distribution.counts?.[tier] ?? 0,
    })).filter((item) => item.value > 0);
  }, [distribution]);

  const supervisorPieData = useMemo(() => {
    if (!distribution) return [];
    return TIERS.map((tier) => ({
      name: tier,
      value: distribution.supervisor_distribution.counts?.[tier] ?? 0,
    })).filter((item) => item.value > 0);
  }, [distribution]);

  const workflowData = useMemo(() => {
    if (!summary) return [];
    const categorized =
      summary.pending_reviews +
      summary.approved_for_doctor +
      summary.completed_cases;
    const other = Math.max(0, summary.total_cases - categorized);

    return [
      { name: "Pending review", value: summary.pending_reviews, fill: "#f59e0b" },
      {
        name: "Approved for doctor",
        value: summary.approved_for_doctor,
        fill: "#3b82f6",
      },
      { name: "Completed", value: summary.completed_cases, fill: "#10b981" },
      { name: "Other / unclassified", value: other, fill: "#94a3b8" },
    ].filter((item) => item.value > 0);
  }, [summary]);

  return (
    <div className="min-h-screen bg-slate-50">
      <Sidebar />

      <main className="ml-64 min-h-screen">
        <Header />

        <div className="space-y-6 p-8">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-slate-800">
                Analytics Dashboard
              </h1>
              <p className="mt-1 text-sm text-slate-500">
                Monitor case volume, workflow progress, and AI–supervisor
                triage agreement.
              </p>
            </div>

            <button
              onClick={fetchAnalytics}
              disabled={loading}
              className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
            >
              <RefreshCw
                size={16}
                className={loading ? "animate-spin" : ""}
              />
              Refresh
            </button>
          </div>

          {error && (
            <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              <AlertCircle size={18} />
              {error}
            </div>
          )}

          {loading && !summary ? (
            <div className="rounded-xl border border-slate-200 bg-white p-10 text-center text-sm text-slate-500">
              Loading analytics...
            </div>
          ) : (
            <>
              <section>
                <div className="mb-3 flex items-center gap-2">
                  <Activity size={18} className="text-blue-600" />
                  <h2 className="font-semibold text-slate-800">
                    Workflow Overview
                  </h2>
                </div>

                <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                  <StatCard
                    title="Total Cases"
                    value={formatNumber(summary?.total_cases)}
                    subtitle="All cases recorded"
                    icon={Users}
                  />
                  <StatCard
                    title="Pending Reviews"
                    value={formatNumber(summary?.pending_reviews)}
                    subtitle="Awaiting supervisor review"
                    icon={Clock}
                  />
                  <StatCard
                    title="Approved for Doctor"
                    value={formatNumber(summary?.approved_for_doctor)}
                    subtitle="Approved and awaiting / in doctor workflow"
                    icon={ShieldCheck}
                  />
                  <StatCard
                    title="Completed Consultations"
                    value={formatNumber(summary?.completed_cases)}
                    subtitle="Cases marked completed"
                    icon={CheckCircle}
                  />
                </div>
              </section>

              <section className="grid gap-4 xl:grid-cols-3">
                <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm xl:col-span-2">
                  <div className="mb-1 flex items-center gap-2">
                    <TrendingUp size={19} className="text-blue-600" />
                    <h2 className="font-semibold text-slate-800">
                      AI vs Supervisor Triage Distribution
                    </h2>
                  </div>
                  <p className="mb-4 text-xs text-slate-500">
                    Counts across all cases with a recorded tier.
                  </p>

                  {comparisonData.some(
                    (item) =>
                      item["AI predictions"] > 0 ||
                      item["Supervisor verified"] > 0
                  ) ? (
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart
                        data={comparisonData}
                        margin={{ top: 10, right: 12, left: 0, bottom: 5 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" vertical={false} />
                        <XAxis dataKey="tier" />
                        <YAxis allowDecimals={false} />
                        <Tooltip />
                        <Legend />
                        <Bar
                          dataKey="AI predictions"
                          fill="#3b82f6"
                          radius={[5, 5, 0, 0]}
                        />
                        <Bar
                          dataKey="Supervisor verified"
                          fill="#8b5cf6"
                          radius={[5, 5, 0, 0]}
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <EmptyChart message="No triage distribution data is available yet." />
                  )}
                </div>

                <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                  <h2 className="font-semibold text-slate-800">
                    Workflow Status
                  </h2>
                  <p className="mb-4 mt-1 text-xs text-slate-500">
                    Distribution of recorded case statuses.
                  </p>
                  {workflowData.length > 0 ? (
                    <>
                      <ResponsiveContainer width="100%" height={245}>
                        <PieChart>
                          <Pie
                            data={workflowData}
                            dataKey="value"
                            nameKey="name"
                            cx="50%"
                            cy="50%"
                            outerRadius={85}
                            label
                          >
                            {workflowData.map((entry) => (
                              <Cell key={entry.name} fill={entry.fill} />
                            ))}
                          </Pie>
                          <Tooltip />
                        </PieChart>
                      </ResponsiveContainer>
                      <div className="space-y-2">
                        {workflowData.map((item) => (
                          <div
                            key={item.name}
                            className="flex items-center justify-between text-xs"
                          >
                            <span className="flex items-center gap-2 text-slate-600">
                              <span
                                className="h-2.5 w-2.5 rounded-full"
                                style={{ backgroundColor: item.fill }}
                              />
                              {item.name}
                            </span>
                            <span className="font-semibold text-slate-800">
                              {item.value}
                            </span>
                          </div>
                        ))}
                      </div>
                    </>
                  ) : (
                    <EmptyChart message="No workflow records are available yet." />
                  )}
                </div>
              </section>

              <section className="grid gap-4 lg:grid-cols-2">
                <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                  <h2 className="font-semibold text-slate-800">
                    AI Prediction Breakdown
                  </h2>
                  <p className="mt-1 text-xs text-slate-500">
                    {distribution?.ai_distribution.total_predictions ?? 0}{" "}
                    recorded AI predictions.
                  </p>
                  {aiPieData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={250}>
                      <PieChart>
                        <Pie
                          data={aiPieData}
                          dataKey="value"
                          nameKey="name"
                          cx="50%"
                          cy="50%"
                          outerRadius={85}
                          label
                        >
                          {aiPieData.map((entry) => (
                            <Cell
                              key={entry.name}
                              fill={TIER_COLORS[entry.name as Tier]}
                            />
                          ))}
                        </Pie>
                        <Tooltip />
                        <Legend />
                      </PieChart>
                    </ResponsiveContainer>
                  ) : (
                    <EmptyChart message="No AI predictions are available yet." />
                  )}
                </div>

                <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                  <h2 className="font-semibold text-slate-800">
                    Supervisor-Verified Breakdown
                  </h2>
                  <p className="mt-1 text-xs text-slate-500">
                    {distribution?.supervisor_distribution.total_verified_cases ??
                      0}{" "}
                    cases with a supervisor-verified tier.
                  </p>
                  {supervisorPieData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={250}>
                      <PieChart>
                        <Pie
                          data={supervisorPieData}
                          dataKey="value"
                          nameKey="name"
                          cx="50%"
                          cy="50%"
                          outerRadius={85}
                          label
                        >
                          {supervisorPieData.map((entry) => (
                            <Cell
                              key={entry.name}
                              fill={TIER_COLORS[entry.name as Tier]}
                            />
                          ))}
                        </Pie>
                        <Tooltip />
                        <Legend />
                      </PieChart>
                    </ResponsiveContainer>
                  ) : (
                    <EmptyChart message="No supervisor-verified tiers are available yet." />
                  )}
                </div>
              </section>

              <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <h2 className="font-semibold text-slate-800">
                      AI–Supervisor Discordance Analysis
                    </h2>
                    <p className="mt-1 max-w-2xl text-xs leading-5 text-slate-500">
                      {discordance?.interpretation ||
                        "Comparison of AI-predicted and supervisor-verified tiers."}
                    </p>
                  </div>
                  <div className="rounded-lg bg-slate-50 px-4 py-3 text-right">
                    <p className="text-xs text-slate-500">Discordance rate</p>
                    <p className="text-2xl font-bold text-slate-800">
                      {discordance
                        ? `${discordance.discordance_rate_percent.toFixed(2)}%`
                        : "—"}
                    </p>
                  </div>
                </div>

                <div className="mt-5 grid gap-4 sm:grid-cols-3">
                  <div className="rounded-lg bg-slate-50 p-4">
                    <p className="text-xs text-slate-500">
                      Reviewed cases with AI prediction
                    </p>
                    <p className="mt-1 text-2xl font-bold text-slate-800">
                      {formatNumber(
                        discordance?.total_reviewed_cases_with_ai_prediction
                      )}
                    </p>
                  </div>
                  <div className="rounded-lg bg-red-50 p-4">
                    <p className="text-xs text-red-600">
                      Discordant cases
                    </p>
                    <p className="mt-1 text-2xl font-bold text-red-700">
                      {formatNumber(discordance?.total_discordant_cases)}
                    </p>
                  </div>
                  <div className="rounded-lg bg-emerald-50 p-4">
                    <p className="text-xs text-emerald-600">
                      Agreement cases
                    </p>
                    <p className="mt-1 text-2xl font-bold text-emerald-700">
                      {formatNumber(discordance?.total_agreement_cases)}
                    </p>
                  </div>
                </div>

                <div className="mt-5">
                  <div className="mb-2 flex justify-between text-xs">
                    <span className="font-medium text-slate-600">
                      Agreement rate
                    </span>
                    <span className="font-semibold text-emerald-700">
                      {discordance
                        ? `${discordance.agreement_rate_percent.toFixed(2)}%`
                        : "—"}
                    </span>
                  </div>
                  <div className="h-3 overflow-hidden rounded-full bg-red-100">
                    <div
                      className="h-full rounded-full bg-emerald-500 transition-all"
                      style={{
                        width: `${Math.min(
                          100,
                          Math.max(0, discordance?.agreement_rate_percent ?? 0)
                        )}%`,
                      }}
                    />
                  </div>
                </div>

                <p className="mt-4 text-xs leading-5 text-slate-400">
                  Discordance is calculated only for reviewed cases with both
                  an AI prediction and a supervisor-verified tier. It measures
                  disagreement, not model error or clinical correctness.
                </p>

                {discordance?.discordant_case_ids?.length ? (
                  <div className="mt-4">
                    <p className="mb-2 text-xs font-semibold text-slate-600">
                      Discordant case IDs
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {discordance.discordant_case_ids.map((id) => (
                        <span
                          key={id}
                          className="rounded-full border border-red-200 bg-red-50 px-3 py-1 text-xs font-medium text-red-700"
                        >
                          Case #{id}
                        </span>
                      ))}
                    </div>
                  </div>
                ) : null}
              </section>
            </>
          )}

          <footer className="pb-4 text-center text-xs text-slate-400">
            SmartTriage AI · Educational prototype · Not clinically validated
          </footer>
        </div>
      </main>
    </div>
  );
}
