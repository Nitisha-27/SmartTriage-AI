
"use client";

import { useEffect, useState } from "react";
import {
  Activity,
  AlertCircle,
  CheckCircle2,
  ClipboardList,
  RefreshCw,
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

type Summary = {
  total_cases: number;
  pending_reviews: number;
  approved_for_doctor: number;
  completed_cases: number;
  total_reviewed_cases: number;
};

type Distribution = {
  total_predictions?: number;
  total_verified_cases?: number;
  counts: Record<string, number>;
  percentages: Record<string, number>;
};

type TriageDistribution = {
  ai_distribution: Distribution;
  supervisor_distribution: Distribution;
};

type Discordance = {
  total_reviewed_cases_with_ai_prediction: number;
  total_discordant_cases: number;
  total_agreement_cases: number;
  discordance_rate_percent: number;
  agreement_rate_percent: number;
  discordant_case_ids: number[];
  interpretation: string;
};

const COLORS: Record<string, string> = {
  Routine: "#16A34A",
  Urgent: "#EAB308",
  Emergent: "#DC2626",
  "1": "#DC2626",
  "2": "#EA580C",
  "3": "#EAB308",
  "4": "#16A34A",
  "5": "#0D9488",
};

const getColor = (label: string) => COLORS[label] || "#64748B";

function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
}: {
  title: string;
  value: number | string;
  subtitle: string;
  icon: React.ElementType;
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-slate-500">{title}</p>
          <h3 className="mt-2 text-3xl font-bold text-slate-900">{value}</h3>
          <p className="mt-2 text-xs text-slate-500">{subtitle}</p>
        </div>
        <div className="rounded-lg bg-blue-50 p-3 text-blue-700">
          <Icon size={22} />
        </div>
      </div>
    </div>
  );
}

function DistributionChart({
  title,
  subtitle,
  distribution,
}: {
  title: string;
  subtitle: string;
  distribution: Distribution;
}) {
const chartData = Object.entries(distribution.counts || {})
  .map(([name, value]) => ({
    name,
    value,
    percentage: distribution.percentages?.[name] ?? 0,
  }))
  .filter((item) => item.value > 0);

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div>
        <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
        <p className="mt-1 text-sm text-slate-500">{subtitle}</p>
      </div>

      {chartData.length === 0 ? (
        <div className="flex h-72 items-center justify-center text-sm text-slate-400">
          No distribution data available.
        </div>
      ) : (
        <>
          <div className="mt-5 h-72">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={chartData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={95}
                  innerRadius={55}
                  paddingAngle={3}

                >
                  {chartData.map((entry) => (
                    <Cell
                      key={entry.name}
                      fill={getColor(entry.name)}
                    />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value, _name, item) => [
                    `${value} cases (${item.payload.percentage}%)`,
                    item.payload.name,
                  ]}
                />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="mt-2 space-y-2">
            {chartData.map((item) => (
              <div
                key={item.name}
                className="flex items-center justify-between text-sm"
              >
                <div className="flex items-center gap-2">
                  <span
                    className="h-3 w-3 rounded-full"
                    style={{ backgroundColor: getColor(item.name) }}
                  />
                  <span className="text-slate-600">{item.name}</span>
                </div>
                <span className="font-semibold text-slate-800">
                  {item.value} ({item.percentage}%)
                </span>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

export default function AnalyticsPage() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [distribution, setDistribution] =
    useState<TriageDistribution | null>(null);
  const [discordance, setDiscordance] =
    useState<Discordance | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchAnalytics = async () => {
    setLoading(true);
    setError("");

    try {
      const [summaryRes, distributionRes, discordanceRes] =
        await Promise.all([
          api.get("/analytics/summary"),
          api.get("/analytics/triage-distribution"),
          api.get("/analytics/discordance"),
        ]);

      setSummary(summaryRes.data);
      setDistribution(distributionRes.data);
      setDiscordance(discordanceRes.data);
    } catch (err) {
      console.error("Analytics loading error:", err);
      setError(
        "Unable to load analytics. Please check whether the backend is running."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const comparisonData =
    distribution &&
    Object.keys({
      ...distribution.ai_distribution.counts,
      ...distribution.supervisor_distribution.counts,
    }).map((tier) => ({
      tier,
      AI: distribution.ai_distribution.counts[tier] ?? 0,
      Supervisor:
        distribution.supervisor_distribution.counts[tier] ?? 0,
    }));

  return (
    <div className="min-h-screen bg-slate-50">
      <Sidebar />

      <main className="min-h-screen md:ml-64">
      <header className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 bg-white px-4 py-5 sm:px-8">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">
              Analytics
            </h1>
            <p className="mt-1 text-sm text-slate-500">
              Monitor triage activity, predictions and supervisor decisions.
            </p>
          </div>

          <button
            onClick={fetchAnalytics}
            disabled={loading}
            className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-100 disabled:opacity-50"
          >
            <RefreshCw
              size={16}
              className={loading ? "animate-spin" : ""}
            />
            Refresh
          </button>
        </header>

       <div className="space-y-8 p-4 sm:p-6 lg:p-8">
          {error && (
            <div className="flex items-center gap-3 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              <AlertCircle size={20} />
              {error}
              <button
                onClick={fetchAnalytics}
                className="ml-auto font-semibold underline"
              >
                Retry
              </button>
            </div>
          )}

          {loading && !summary ? (
            <div className="flex h-64 items-center justify-center text-slate-500">
              <RefreshCw className="mr-3 animate-spin" size={20} />
              Loading analytics...
            </div>
          ) : summary && discordance && distribution ? (
            <>
              <section>
                <div className="mb-4 flex items-center gap-2">
                  <Activity className="text-blue-700" size={20} />
                  <h2 className="text-lg font-semibold text-slate-900">
                    Case Overview
                  </h2>
                </div>

                <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-4">
                  <StatCard
                    title="Total Cases"
                    value={summary.total_cases}
                    subtitle="All submitted patient cases"
                    icon={Users}
                  />
                  <StatCard
                    title="Pending Reviews"
                    value={summary.pending_reviews}
                    subtitle="Awaiting supervisor review"
                    icon={ClipboardList}
                  />
                  <StatCard
                    title="Approved for Doctor"
                    value={summary.approved_for_doctor}
                    subtitle="Cases cleared for consultation"
                    icon={Activity}
                  />
                  <StatCard
                    title="Completed Cases"
                    value={summary.completed_cases}
                    subtitle="Consultations completed"
                    icon={CheckCircle2}
                  />
                </div>
              </section>

              <section>
                <div className="mb-4 flex items-center gap-2">
                  <TrendingUp className="text-blue-700" size={20} />
                  <h2 className="text-lg font-semibold text-slate-900">
                    Triage Distribution
                  </h2>
                </div>

                <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
                  <DistributionChart
                    title="AI Predictions"
                    subtitle={`${distribution.ai_distribution.total_predictions ?? 0} AI-generated assessments`}
                    distribution={distribution.ai_distribution}
                  />

                  <DistributionChart
                    title="Supervisor Decisions"
                    subtitle={`${distribution.supervisor_distribution.total_verified_cases ?? 0} reviewed cases`}
                    distribution={distribution.supervisor_distribution}
                  />
                </div>
              </section>

              <section className="grid grid-cols-1 gap-6 xl:grid-cols-3">
                <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm xl:col-span-2">
                  <h3 className="text-lg font-semibold text-slate-900">
                    AI vs Supervisor Comparison
                  </h3>
                  <p className="mt-1 text-sm text-slate-500">
                    Comparison of triage category counts.
                  </p>

                  <div className="mt-6 h-72">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={comparisonData || []}>
                        <CartesianGrid
                          strokeDasharray="3 3"
                          vertical={false}
                        />
                        <XAxis dataKey="tier" />
                        <YAxis allowDecimals={false} />
                        <Tooltip />
                        <Legend />
                        <Bar
                          dataKey="AI"
                          fill="#2563EB"
                          radius={[5, 5, 0, 0]}
                        />
                        <Bar
                          dataKey="Supervisor"
                          fill="#0F766E"
                          radius={[5, 5, 0, 0]}
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
                  <h3 className="text-lg font-semibold text-slate-900">
                    Supervisor Review
                  </h3>
                  <p className="mt-1 text-sm text-slate-500">
                    AI and human decision agreement.
                  </p>

                  <div className="mt-6">
                    <p className="text-sm text-slate-500">
                      Agreement Rate
                    </p>
                    <p className="mt-1 text-4xl font-bold text-green-600">
                      {discordance.agreement_rate_percent.toFixed(2)}%
                    </p>

                    <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-100">
                      <div
                        className="h-full rounded-full bg-green-500"
                        style={{
                          width: `${Math.min(
                            100,
                            Math.max(0, discordance.agreement_rate_percent)
                          )}%`,
                        }}
                      />
                    </div>
                  </div>

                  <div className="mt-8">
                    <p className="text-sm text-slate-500">
                      Override / Discordance Rate
                    </p>
                    <p className="mt-1 text-3xl font-bold text-red-600">
                      {discordance.discordance_rate_percent.toFixed(2)}%
                    </p>
                  </div>

                  <div className="mt-8 space-y-3 border-t border-slate-100 pt-5">
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-500">
                        Reviewed cases
                      </span>
                      <span className="font-semibold text-slate-800">
                        {discordance.total_reviewed_cases_with_ai_prediction}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-500">
                        Agreements
                      </span>
                      <span className="font-semibold text-green-700">
                        {discordance.total_agreement_cases}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-500">
                        Overrides
                      </span>
                      <span className="font-semibold text-red-700">
                        {discordance.total_discordant_cases}
                      </span>
                    </div>
                  </div>
                </div>
              </section>

              <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
                <div className="flex items-center gap-2">
                  <AlertCircle size={20} className="text-amber-600" />
                  <h3 className="text-lg font-semibold text-slate-900">
                    Supervisor Overrides
                  </h3>
                </div>

                <p className="mt-1 text-sm text-slate-500">
                  Cases where the supervisor selected a different triage
                  category from the AI recommendation.
                </p>

                {discordance.discordant_case_ids.length === 0 ? (
                  <p className="mt-5 rounded-lg bg-slate-50 p-4 text-sm text-slate-500">
                    No supervisor overrides recorded.
                  </p>
                ) : (
                  <div className="mt-5 flex flex-wrap gap-3">
                    {discordance.discordant_case_ids.map((id) => (
                      <span
                        key={id}
                        className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-2 text-sm font-semibold text-amber-800"
                      >
                        Case #{id}
                      </span>
                    ))}
                  </div>
                )}

                <p className="mt-5 text-xs text-slate-400">
                  {discordance.interpretation}
                </p>
              </section>

              <p className="text-xs text-slate-400">
                These statistics describe workflow activity and agreement
                within this prototype. They do not establish clinical
                accuracy or safety.
              </p>
            </>
          ) : (
            !error && (
              <div className="rounded-xl border border-slate-200 bg-white p-8 text-center text-slate-500">
                Analytics data is not available yet.
              </div>
            )
          )}
        </div>
      </main>
    </div>
  );
}
