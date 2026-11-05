
"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

interface TriageChartProps {
  aiCounts: Record<string, number>;
  supervisorCounts: Record<string, number>;
}

export default function TriageChart({
  aiCounts,
  supervisorCounts,
}: TriageChartProps) {
  const data = ["Emergent", "Urgent", "Routine"].map((tier) => ({
    tier,
    AI: aiCounts[tier] ?? 0,
    Supervisor: supervisorCounts[tier] ?? 0,
  }));

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-slate-800">
          Triage Distribution
        </h3>
        <p className="mt-1 text-sm text-slate-500">
          AI predictions compared with supervisor decisions
        </p>
      </div>

      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} barGap={8}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="tier" axisLine={false} tickLine={false} />
            <YAxis allowDecimals={false} axisLine={false} tickLine={false} />
            <Tooltip />
            <Legend />
            <Bar dataKey="AI" fill="#3B82F6" radius={[5, 5, 0, 0]} />
            <Bar
              dataKey="Supervisor"
              fill="#10B981"
              radius={[5, 5, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
