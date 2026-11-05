
import { Clock, UserRound } from "lucide-react";

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

interface RecentCasesProps {
  cases: PatientCase[];
}

const tierStyles: Record<string, string> = {
  Emergent: "bg-red-100 text-red-700",
  Urgent: "bg-amber-100 text-amber-700",
  Routine: "bg-emerald-100 text-emerald-700",
};

export default function RecentCases({ cases }: RecentCasesProps) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-100 p-6">
        <div>
          <h3 className="text-lg font-semibold text-slate-800">
            Doctor Queue
          </h3>
          <p className="mt-1 text-sm text-slate-500">
            Supervisor-approved cases awaiting consultation
          </p>
        </div>

        <span className="rounded-lg bg-blue-50 px-3 py-1.5 text-sm font-medium text-blue-700">
          {cases.length} cases
        </span>
      </div>

      {cases.length === 0 ? (
        <div className="flex flex-col items-center justify-center px-6 py-12 text-center">
          <UserRound size={32} className="text-slate-300" />
          <p className="mt-3 font-medium text-slate-600">
            No cases in the doctor queue
          </p>
          <p className="mt-1 text-sm text-slate-400">
            Approved cases will appear here.
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-slate-500">
              <tr>
                <th className="px-6 py-4">Patient</th>
                <th className="px-6 py-4">Syndrome</th>
                <th className="px-6 py-4">AI Tier</th>
                <th className="px-6 py-4">Verified Tier</th>
                <th className="px-6 py-4">Status</th>
              </tr>
            </thead>

            <tbody className="divide-y divide-slate-100">
              {cases.map((item) => (
                <tr key={item.case_id} className="hover:bg-slate-50">
                  <td className="px-6 py-4">
                    <p className="font-medium text-slate-800">
                      {item.patient_name}
                    </p>
                    <p className="mt-1 text-xs text-slate-500">
                      {item.age} years · {item.gender}
                    </p>
                  </td>

                  <td className="px-6 py-4 text-slate-600">
                    {item.syndrome_match || "Not specified"}
                  </td>

                  <td className="px-6 py-4">
                    <span
                      className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
                        tierStyles[item.ai_triage_tier || ""] ||
                        "bg-slate-100 text-slate-600"
                      }`}
                    >
                      {item.ai_triage_tier || "Unavailable"}
                    </span>
                  </td>

                  <td className="px-6 py-4">
                    <span
                      className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
                        tierStyles[item.human_verified_tier || ""] ||
                        "bg-slate-100 text-slate-600"
                      }`}
                    >
                      {item.human_verified_tier || "Pending"}
                    </span>
                  </td>

                  <td className="px-6 py-4">
                    <span className="inline-flex items-center gap-1.5 text-xs text-blue-700">
                      <Clock size={13} />
                      Awaiting consultation
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
