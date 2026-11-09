
"use client";

import { useCallback, useEffect, useState } from "react";
import {
  AlertCircle,
  CheckCircle,
  ClipboardCheck,
  RefreshCw,
  UserRound,
  Activity,
  FileText,
  AlertTriangle,
  Clock,
} from "lucide-react";

import api from "@/lib/api";
import Sidebar from "@/components/Sidebar";
import Header from "@/components/Header";

type TriageTier = "Routine" | "Urgent" | "Emergent";
type ReviewAction = "APPROVE" | "OVERRIDE";

interface SafetyAlert {
  code: string;
  category: string;
  message: string;
  severity: string;
  source: string;
}

interface SafetyAssessment {
  alerts: SafetyAlert[];
  alert_count: number;
  has_safety_alert: boolean;
  engine: string;
  notice: string;
}

interface PatientCase {
  case_id: number;
  patient_name: string;
  age: number;
  gender: string;
  raw_narrative: string;
  ai_triage_tier: TriageTier | null;
  ai_confidence: number | null;
  syndrome_match: string | null;
  syndrome_similarity: number | null;
  news2_score: number | null;
  detected_red_flags: Record<string, string> | null;
  missing_fields: string[] | null;
  shap_explanation: unknown;
  safety_assessment: SafetyAssessment | null;
  status: string;
  created_at: string;
}

const tiers: TriageTier[] = ["Routine", "Urgent", "Emergent"];

function tierStyle(tier: string | null) {
  switch (tier) {
    case "Emergent":
      return "bg-red-100 text-red-700 border-red-200";
    case "Urgent":
      return "bg-amber-100 text-amber-700 border-amber-200";
    case "Routine":
      return "bg-emerald-100 text-emerald-700 border-emerald-200";
    default:
      return "bg-slate-100 text-slate-600 border-slate-200";
  }
}

function formatDate(value: string) {
  if (!value) return "Date unavailable";

  return new Date(value).toLocaleString();
}

export default function SupervisorPage() {
  const [cases, setCases] = useState<PatientCase[]>([]);
  const [selectedCase, setSelectedCase] =
    useState<PatientCase | null>(null);

  const [action, setAction] =
    useState<ReviewAction>("APPROVE");

  const [verifiedTier, setVerifiedTier] =
    useState<TriageTier>("Urgent");

  const [comment, setComment] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const fetchPendingCases = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const response = await api.get("/cases/pending");
      const pendingCases: PatientCase[] =
        response.data.cases || [];

      setCases(pendingCases);

      setSelectedCase((current) => {
        if (!current) {
          return pendingCases.length > 0
            ? pendingCases[0]
            : null;
        }

        return (
          pendingCases.find(
            (item) => item.case_id === current.case_id
          ) || pendingCases[0] || null
        );
      });
    } catch (err) {
      console.error("Pending cases error:", err);
      setError("Unable to load pending cases. Check the backend connection.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPendingCases();
  }, [fetchPendingCases]);

  useEffect(() => {
    if (!selectedCase) return;

    setVerifiedTier(
      selectedCase.ai_triage_tier || "Urgent"
    );

    setAction(
      selectedCase.ai_triage_tier ? "APPROVE" : "OVERRIDE"
    );

    setComment("");
    setSuccess("");
  }, [selectedCase?.case_id]);

  const handleReview = async () => {
    if (!selectedCase) return;

    if (!comment.trim()) {
      setError("Please enter a supervisor review comment.");
      return;
    }

    if (
      action === "APPROVE" &&
      !selectedCase.ai_triage_tier
    ) {
      setError(
        "This case has no AI prediction. Please use OVERRIDE."
      );
      return;
    }

    if (
      action === "OVERRIDE" &&
      verifiedTier === selectedCase.ai_triage_tier
    ) {
      setError(
        "Select a different tier to override the AI recommendation."
      );
      return;
    }

    const finalTier =
      action === "APPROVE"
        ? selectedCase.ai_triage_tier
        : verifiedTier;

    if (!finalTier) return;

    setSubmitting(true);
    setError("");
    setSuccess("");

    try {
      const response = await api.post(
        "/cases/supervisor/review",
        {
          case_id: selectedCase.case_id,
          action,
          verified_tier: finalTier,
          comment: comment.trim(),
        }
      );

      setSuccess(
        `Case #${response.data.case_id} reviewed successfully.`
      );

      setComment("");

      await fetchPendingCases();
    } catch (err: any) {
      console.error("Supervisor review error:", err);

      setError(
        err?.response?.data?.detail ||
        "Unable to submit the supervisor review."
      );
    } finally {
      setSubmitting(false);
    }
  };

  const shapData = Array.isArray(
    selectedCase?.shap_explanation
  )
    ? selectedCase.shap_explanation
    : [];

  const redFlagEntries = Object.entries(
    selectedCase?.detected_red_flags || {}
  );

  const safetyAssessment = selectedCase?.safety_assessment;
  const safetyAlerts = safetyAssessment?.alerts || [];

  return (
    <div className="min-h-screen bg-slate-50">
      <Sidebar />

      <main className="ml-64 min-h-screen">
        <Header />

        <div className="space-y-6 p-8">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-slate-800">
                Supervisor Review
              </h1>

              <p className="mt-1 text-sm text-slate-500">
                Review AI-generated patient assessments and record
                supervisor decisions.
              </p>
            </div>

            <button
              onClick={fetchPendingCases}
              disabled={loading}
              className="flex items-center gap-2 rounded-lg border bg-white px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
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

          {success && (
            <div className="flex items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-700">
              <CheckCircle size={18} />
              {success}
            </div>
          )}

          <div className="grid gap-6 xl:grid-cols-3">
            {/* Pending case list */}
            <section className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="font-semibold text-slate-800">
                  Pending Cases
                </h2>

                <span className="rounded-full bg-blue-100 px-3 py-1 text-xs font-semibold text-blue-700">
                  {cases.length} pending
                </span>
              </div>

              {loading ? (
                <div className="rounded-xl border bg-white p-8 text-center text-sm text-slate-500">
                  Loading pending cases...
                </div>
              ) : cases.length === 0 ? (
                <div className="rounded-xl border bg-white p-8 text-center">
                  <CheckCircle
                    size={32}
                    className="mx-auto text-emerald-500"
                  />

                  <p className="mt-3 font-semibold text-slate-700">
                    No pending reviews
                  </p>

                  <p className="mt-1 text-sm text-slate-500">
                    New patient assessments will appear here.
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {cases.map((item) => (
                    <button
                      key={item.case_id}
                      onClick={() => {
                        setSelectedCase(item);
                        setError("");
                        setSuccess("");
                      }}
                      className={`w-full rounded-xl border bg-white p-4 text-left shadow-sm transition hover:border-blue-300 ${
                        selectedCase?.case_id === item.case_id
                          ? "border-blue-500 ring-2 ring-blue-100"
                          : "border-slate-200"
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <p className="font-semibold text-slate-800">
                            {item.patient_name}
                          </p>

                          <p className="mt-1 text-xs text-slate-500">
                            Case #{item.case_id} · {item.age} years ·{" "}
                            {item.gender}
                          </p>
                        </div>

                        <span
                          className={`rounded-full border px-2.5 py-1 text-xs font-semibold ${tierStyle(
                            item.ai_triage_tier
                          )}`}
                        >
                          {item.ai_triage_tier || "No AI tier"}
                        </span>
                      </div>

                      <p className="mt-3 line-clamp-2 text-sm text-slate-600">
                        {item.raw_narrative}
                      </p>

                      <div className="mt-3 flex items-center gap-2 text-xs text-slate-400">
                        <Clock size={13} />
                        {formatDate(item.created_at)}
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </section>

            {/* Selected case details */}
            <section className="space-y-4 xl:col-span-2">
              <h2 className="font-semibold text-slate-800">
                Assessment Details
              </h2>

              {!selectedCase ? (
                <div className="rounded-xl border bg-white p-12 text-center text-slate-500">
                  Select a pending case to review its assessment.
                </div>
              ) : (
                <>
                  {/* Patient information */}
                  <div className="rounded-xl border bg-white p-6 shadow-sm">
                    <div className="flex items-center gap-3">
                      <div className="rounded-lg bg-blue-50 p-3 text-blue-600">
                        <UserRound size={22} />
                      </div>

                      <div>
                        <h3 className="font-semibold text-slate-800">
                          {selectedCase.patient_name}
                        </h3>

                        <p className="text-sm text-slate-500">
                          Case #{selectedCase.case_id} ·{" "}
                          {selectedCase.age} years ·{" "}
                          {selectedCase.gender}
                        </p>
                      </div>
                    </div>

                    <div className="mt-5 grid gap-4 sm:grid-cols-2">
                      <div className="rounded-lg bg-slate-50 p-4">
                        <p className="text-xs text-slate-500">
                          AI Triage Recommendation
                        </p>

                        <span
                          className={`mt-2 inline-block rounded-full border px-3 py-1 text-sm font-semibold ${tierStyle(
                            selectedCase.ai_triage_tier
                          )}`}
                        >
                          {selectedCase.ai_triage_tier ||
                            "Unavailable"}
                        </span>
                      </div>

                      <div className="rounded-lg bg-slate-50 p-4">
                        <p className="text-xs text-slate-500">
                          AI Confidence
                        </p>

                        <p className="mt-2 text-xl font-bold text-slate-800">
                          {selectedCase.ai_confidence != null
                            ? `${(
                                selectedCase.ai_confidence * 100
                              ).toFixed(1)}%`
                            : "Unavailable"}
                        </p>
                      </div>

                      <div className="rounded-lg bg-slate-50 p-4">
                        <p className="text-xs text-slate-500">
                          Syndrome Match
                        </p>

                        <p className="mt-2 font-semibold text-slate-800">
                          {selectedCase.syndrome_match ||
                            "Unavailable"}
                        </p>
                      </div>

                      <div className="rounded-lg bg-slate-50 p-4">
                        <p className="text-xs text-slate-500">
                          Five-parameter score
                        </p>

                        <p className="mt-2 text-xl font-bold text-slate-800">
                          {selectedCase.news2_score ?? "Unavailable"}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Clinical narrative */}
                  <div className="rounded-xl border bg-white p-6 shadow-sm">
                    <div className="mb-3 flex items-center gap-2">
                      <FileText
                        size={19}
                        className="text-blue-600"
                      />

                      <h3 className="font-semibold text-slate-800">
                        Clinical Narrative
                      </h3>
                    </div>

                    <p className="whitespace-pre-wrap text-sm leading-7 text-slate-600">
                      {selectedCase.raw_narrative}
                    </p>
                  </div>

                  {/* Independent safety alerts */}
                  <div
                    className={`rounded-xl border p-6 shadow-sm ${
                      safetyAssessment?.has_safety_alert
                        ? "border-red-300 bg-red-50"
                        : "border-slate-200 bg-white"
                    }`}
                  >
                    <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                      <div className="flex items-center gap-2">
                        <AlertTriangle
                          size={19}
                          className={
                            safetyAssessment?.has_safety_alert
                              ? "text-red-600"
                              : "text-slate-500"
                          }
                        />
                        <h3 className="font-semibold text-slate-800">
                          Independent Safety Alerts
                        </h3>
                      </div>

                      {safetyAssessment && (
                        <span
                          className={`rounded-full border px-3 py-1 text-xs font-semibold ${
                            safetyAssessment.has_safety_alert
                              ? "border-red-300 bg-white text-red-700"
                              : "border-slate-300 bg-slate-50 text-slate-600"
                          }`}
                        >
                          {safetyAssessment.alert_count} alert
                          {safetyAssessment.alert_count === 1 ? "" : "s"}
                        </span>
                      )}
                    </div>

                    {!safetyAssessment ? (
                      <p className="text-sm text-slate-600">
                        Safety assessment unavailable for this case. It may
                        have been created before the independent safety engine
                        was added. Do not interpret missing data as absence of
                        risk.
                      </p>
                    ) : safetyAlerts.length > 0 ? (
                      <div className="space-y-3">
                        {safetyAlerts.map((alert, index) => (
                          <div
                            key={`${alert.code}-${index}`}
                            className="rounded-lg border border-red-200 bg-white p-4"
                          >
                            <div className="flex flex-wrap items-start justify-between gap-2">
                              <div>
                                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                                  {alert.category}
                                </p>
                                <p className="mt-1 text-sm font-semibold text-slate-800">
                                  {alert.code.replaceAll("_", " ")}
                                </p>
                              </div>

                              <span
                                className={`rounded-full border px-2.5 py-1 text-xs font-bold ${
                                  alert.severity === "HIGH"
                                    ? "border-red-300 bg-red-100 text-red-800"
                                    : alert.severity === "MODERATE"
                                    ? "border-amber-300 bg-amber-100 text-amber-800"
                                    : "border-slate-300 bg-slate-100 text-slate-700"
                                }`}
                              >
                                {alert.severity}
                              </span>
                            </div>

                            <p className="mt-2 text-sm leading-6 text-slate-700">
                              {alert.message}
                            </p>
                            <p className="mt-2 text-xs text-slate-400">
                              Source: {alert.source}
                            </p>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-slate-600">
                        The prototype safety engine did not generate alerts
                        for this case. This does not establish that the case
                        is safe or replace professional assessment.
                      </p>
                    )}

                    {safetyAssessment?.notice && (
                      <p className="mt-4 border-t border-slate-200 pt-3 text-xs leading-5 text-slate-500">
                        {safetyAssessment.notice}
                      </p>
                    )}
                  </div>

                  {/* Red flags */}
                  <div className="rounded-xl border bg-white p-6 shadow-sm">
                    <div className="mb-3 flex items-center gap-2">
                      <AlertTriangle
                        size={19}
                        className="text-red-500"
                      />

                      <h3 className="font-semibold text-slate-800">
                        Detected Red Flags
                      </h3>
                    </div>

                    {redFlagEntries.length > 0 ? (
                      <div className="space-y-2">
                        {redFlagEntries.map(([flag, description]) => (
                          <div
                            key={flag}
                            className="rounded-lg border border-red-200 bg-red-50 p-3"
                          >
                            <p className="text-sm font-semibold text-red-800">
                              {flag}
                            </p>
                            <p className="mt-1 text-xs text-red-700">
                              {description}
                            </p>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-slate-500">
                        No NLP red flags were recorded for this case. This does not establish that the case is safe.
                      </p>
                    )}
                  </div>

                  {/* Missing information */}
                  <div className="rounded-xl border bg-white p-6 shadow-sm">
                    <div className="mb-3 flex items-center gap-2">
                      <ClipboardCheck
                        size={19}
                        className="text-amber-600"
                      />

                      <h3 className="font-semibold text-slate-800">
                        Missing Clinical Information
                      </h3>
                    </div>

                    {selectedCase.missing_fields?.length ? (
                      <div className="flex flex-wrap gap-2">
                        {selectedCase.missing_fields.map(
                          (field) => (
                            <span
                              key={field}
                              className="rounded-full border border-amber-200 bg-amber-50 px-3 py-1.5 text-xs text-amber-700"
                            >
                              {field.replaceAll("_", " ")}
                            </span>
                          )
                        )}
                      </div>
                    ) : (
                      <p className="text-sm text-emerald-600">
                        No missing fields detected.
                      </p>
                    )}
                  </div>

                  {/* SHAP explanation */}
                  <div className="rounded-xl border bg-white p-6 shadow-sm">
                    <div className="mb-3 flex items-center gap-2">
                      <Activity
                        size={19}
                        className="text-purple-600"
                      />

                      <h3 className="font-semibold text-slate-800">
                        Model Explanation (SHAP)
                      </h3>
                    </div>

                    {shapData.length > 0 ? (
                      <pre className="max-h-64 overflow-auto rounded-lg bg-slate-50 p-4 text-xs text-slate-700">
                        {JSON.stringify(shapData, null, 2)}
                      </pre>
                    ) : (
                      <p className="text-sm text-slate-500">
                        No SHAP explanation is available for this case.
                      </p>
                    )}

                    <p className="mt-3 text-xs text-slate-400">
                      SHAP values describe model contributions; they
                      do not establish clinical causation.
                    </p>
                  </div>

                  {/* Supervisor decision */}
                  <div className="rounded-xl border border-blue-200 bg-white p-6 shadow-sm">
                    <h3 className="text-lg font-semibold text-slate-800">
                      Supervisor Decision
                    </h3>

                    <p className="mt-1 text-sm text-slate-500">
                      Review the assessment and record your decision.
                    </p>

                    {!selectedCase.ai_triage_tier && (
                      <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
                        This case has no AI triage prediction. Approval
                        is unavailable; assign a tier using OVERRIDE.
                      </div>
                    )}

                    <div className="mt-5">
                      <label className="mb-2 block text-sm font-medium text-slate-700">
                        Review action
                      </label>

                      <div className="grid grid-cols-2 gap-3">
                        <button
                          type="button"
                          disabled={!selectedCase.ai_triage_tier}
                          onClick={() => {
                            setAction("APPROVE");
                            setVerifiedTier(
                              selectedCase.ai_triage_tier || "Urgent"
                            );
                          }}
                          className={`rounded-lg border p-3 text-sm font-semibold disabled:cursor-not-allowed disabled:opacity-40 ${
                            action === "APPROVE"
                              ? "border-emerald-500 bg-emerald-50 text-emerald-700"
                              : "border-slate-200 text-slate-600"
                          }`}
                        >
                          <CheckCircle
                            size={17}
                            className="mx-auto mb-1"
                          />
                          Approve AI tier
                        </button>

                        <button
                          type="button"
                          onClick={() => setAction("OVERRIDE")}
                          className={`rounded-lg border p-3 text-sm font-semibold ${
                            action === "OVERRIDE"
                              ? "border-amber-500 bg-amber-50 text-amber-700"
                              : "border-slate-200 text-slate-600"
                          }`}
                        >
                          <AlertTriangle
                            size={17}
                            className="mx-auto mb-1"
                          />
                          Override AI tier
                        </button>
                      </div>
                    </div>

                    <div className="mt-5">
                      <label
                        htmlFor="verifiedTier"
                        className="mb-2 block text-sm font-medium text-slate-700"
                      >
                        Supervisor-verified triage tier
                      </label>

                      <select
                        id="verifiedTier"
                        value={verifiedTier}
                        onChange={(event) =>
                          setVerifiedTier(
                            event.target.value as TriageTier
                          )
                        }
                        disabled={action === "APPROVE"}
                        className="w-full rounded-lg border border-slate-300 bg-white px-4 py-3 text-sm disabled:bg-slate-100"
                      >
                        {tiers.map((tier) => (
                          <option key={tier} value={tier}>
                            {tier}
                          </option>
                        ))}
                      </select>

                      {action === "APPROVE" && (
                        <p className="mt-1 text-xs text-slate-400">
                          Approval retains the AI-recommended tier.
                        </p>
                      )}
                    </div>

                    <div className="mt-5">
                      <label
                        htmlFor="supervisorComment"
                        className="mb-2 block text-sm font-medium text-slate-700"
                      >
                        Supervisor comment *
                      </label>

                      <textarea
                        id="supervisorComment"
                        rows={4}
                        value={comment}
                        onChange={(event) =>
                          setComment(event.target.value)
                        }
                        placeholder="Explain the reason for your approval or override..."
                        className="w-full rounded-lg border border-slate-300 px-4 py-3 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                      />
                    </div>

                    <button
                      onClick={handleReview}
                      disabled={
                        submitting ||
                        !comment.trim() ||
                        (action === "OVERRIDE" &&
                          verifiedTier === selectedCase.ai_triage_tier)
                      }
                      className="mt-5 flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 px-5 py-3 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {submitting ? (
                        <>
                          <RefreshCw
                            size={17}
                            className="animate-spin"
                          />
                          Submitting review...
                        </>
                      ) : (
                        <>
                          <CheckCircle size={17} />
                          Submit Supervisor Review
                        </>
                      )}
                    </button>
                  </div>
                </>
              )}
            </section>
          </div>

          <footer className="pb-4 text-center text-xs text-slate-400">
            SmartTriage AI · Educational prototype · Not clinically validated
          </footer>
        </div>
      </main>
    </div>
  );
}
