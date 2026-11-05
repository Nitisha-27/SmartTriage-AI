
"use client";

import { useCallback, useEffect, useState } from "react";
import {
  Stethoscope,
  RefreshCw,
  UserRound,
  Activity,
  FileText,
  CheckCircle,
  AlertTriangle,
  ClipboardList,
  Clock,
  Hospital,
  ShieldCheck,
} from "lucide-react";

import api from "@/lib/api";
import Sidebar from "@/components/Sidebar";
import Header from "@/components/Header";

type TriageTier = "Routine" | "Urgent" | "Emergent";

interface QueueCase {
  case_id: number;
  patient_name: string;
  age: number;
  gender: string;
  ai_triage_tier: TriageTier | null;
  human_verified_tier: TriageTier | null;
  news2_score: number | null;
  syndrome_match: string | null;
  status: string;
  created_at: string;
}

interface CaseDetails {
  case_id: number;
  patient_name: string;
  age: number;
  gender: string;
  raw_narrative: string;

  vitals: {
    heart_rate: number | null;
    resp_rate: number | null;
    systolic_bp: number | null;
    spo2: number | null;
    temperature: number | null;
  };

  clinical_analysis: {
    entities: unknown;
    red_flags: string[] | null;
    missing_fields: string[] | null;
    syndrome: string | null;
    syndrome_similarity: number | null;
  };

  vital_assessment: {
    five_parameter_score: number | null;
  };

  ai_triage_tier: TriageTier | null;
  ai_confidence: number | null;
  shap_explanation: unknown;

  human_verified_tier: TriageTier | null;
  supervisor_comment: string | null;

  soap: {
    subjective: string | null;
    objective: string | null;
    assessment: string | null;
  };

  doctor_notes: string | null;
  referral_facility: string | null;
  status: string;
  created_at: string;
}

function tierStyle(tier: string | null) {
  switch (tier) {
    case "Emergent":
      return "border-red-200 bg-red-50 text-red-700";
    case "Urgent":
      return "border-amber-200 bg-amber-50 text-amber-700";
    case "Routine":
      return "border-emerald-200 bg-emerald-50 text-emerald-700";
    default:
      return "border-slate-200 bg-slate-100 text-slate-600";
  }
}

function formatDate(value: string) {
  if (!value) return "Unavailable";
  return new Date(value).toLocaleString();
}

function DetailCard({
  title,
  value,
}: {
  title: string;
  value: string | number | null | undefined;
}) {
  return (
    <div className="rounded-lg bg-slate-50 p-4">
      <p className="text-xs text-slate-500">{title}</p>
      <p className="mt-2 text-lg font-semibold text-slate-800">
        {value ?? "Unavailable"}
      </p>
    </div>
  );
}

export default function DoctorPage() {
  const [cases, setCases] = useState<QueueCase[]>([]);
  const [selectedCase, setSelectedCase] =
    useState<CaseDetails | null>(null);

  const [loading, setLoading] = useState(true);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [doctorNotes, setDoctorNotes] = useState("");
  const [referralFacility, setReferralFacility] = useState("");

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const fetchQueue = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const response = await api.get("/cases/queue");
      const queue: QueueCase[] = response.data.cases || [];

      setCases(queue);

      if (
        selectedCase &&
        !queue.some(
          (item) => item.case_id === selectedCase.case_id
        )
      ) {
        setSelectedCase(null);
      }
    } catch (err) {
      console.error("Doctor queue error:", err);
      setError("Unable to load the doctor queue. Check the backend connection.");
    } finally {
      setLoading(false);
    }
  }, [selectedCase]);

  const fetchCaseDetails = async (caseId: number) => {
    setDetailsLoading(true);
    setError("");
    setSuccess("");

    try {
      const response = await api.get(`/cases/${caseId}`);

      setSelectedCase(response.data);
      setDoctorNotes(response.data.doctor_notes || "");
      setReferralFacility(
        response.data.referral_facility || ""
      );
    } catch (err) {
      console.error("Case details error:", err);
      setError("Unable to retrieve patient details.");
    } finally {
      setDetailsLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();
    // Initial queue load.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleComplete = async () => {
    if (!selectedCase) return;

    if (!doctorNotes.trim()) {
      setError("Doctor consultation notes are mandatory.");
      return;
    }

    setSubmitting(true);
    setError("");
    setSuccess("");

    try {
      const response = await api.post(
        "/cases/doctor/complete",
        {
          case_id: selectedCase.case_id,
          doctor_notes: doctorNotes.trim(),
          referral_facility: referralFacility.trim() || null,
        }
      );

      setSuccess(
        `Consultation for Case #${response.data.case_id} completed successfully.`
      );

      setSelectedCase(null);
      setDoctorNotes("");
      setReferralFacility("");

      await fetchQueue();
    } catch (err: any) {
      console.error("Consultation completion error:", err);

      setError(
        err?.response?.data?.detail ||
        "Unable to complete the consultation."
      );
    } finally {
      setSubmitting(false);
    }
  };

  const redFlags =
    selectedCase?.clinical_analysis?.red_flags || [];

  const missingFields =
    selectedCase?.clinical_analysis?.missing_fields || [];

  return (
    <div className="min-h-screen bg-slate-50">
      <Sidebar />

      <main className="ml-64 min-h-screen">
        <Header />

        <div className="space-y-6 p-8">
          {/* Header */}
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-slate-800">
                Doctor Queue
              </h1>

              <p className="mt-1 text-sm text-slate-500">
                Review supervisor-approved cases and record consultations.
              </p>
            </div>

            <button
              onClick={fetchQueue}
              disabled={loading}
              className="flex items-center gap-2 rounded-lg border bg-white px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
            >
              <RefreshCw
                size={16}
                className={loading ? "animate-spin" : ""}
              />
              Refresh Queue
            </button>
          </div>

          {error && (
            <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              {error}
            </div>
          )}

          {success && (
            <div className="flex items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-700">
              <CheckCircle size={18} />
              {success}
            </div>
          )}

          {/* Queue summary */}
          <div className="grid gap-4 sm:grid-cols-3">
            <DetailCard
              title="Cases Awaiting Consultation"
              value={cases.length}
            />

            <DetailCard
              title="Emergent Cases"
              value={
                cases.filter(
                  (item) =>
                    item.human_verified_tier === "Emergent"
                ).length
              }
            />

            <DetailCard
              title="Urgent Cases"
              value={
                cases.filter(
                  (item) =>
                    item.human_verified_tier === "Urgent"
                ).length
              }
            />
          </div>

          <div className="grid gap-6 xl:grid-cols-3">
            {/* Doctor queue */}
            <section className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="font-semibold text-slate-800">
                  Approved Cases
                </h2>

                <span className="rounded-full bg-blue-100 px-3 py-1 text-xs font-semibold text-blue-700">
                  {cases.length} cases
                </span>
              </div>

              {loading ? (
                <div className="rounded-xl border bg-white p-8 text-center text-sm text-slate-500">
                  Loading doctor queue...
                </div>
              ) : cases.length === 0 ? (
                <div className="rounded-xl border bg-white p-8 text-center">
                  <CheckCircle
                    size={32}
                    className="mx-auto text-emerald-500"
                  />

                  <p className="mt-3 font-semibold text-slate-700">
                    Queue is empty
                  </p>

                  <p className="mt-1 text-sm text-slate-500">
                    Supervisor-approved cases will appear here.
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {cases.map((item) => (
                    <button
                      key={item.case_id}
                      onClick={() =>
                        fetchCaseDetails(item.case_id)
                      }
                      className={`w-full rounded-xl border bg-white p-4 text-left shadow-sm transition hover:border-blue-300 ${
                        selectedCase?.case_id === item.case_id
                          ? "border-blue-500 ring-2 ring-blue-100"
                          : "border-slate-200"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
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
                            item.human_verified_tier
                          )}`}
                        >
                          {item.human_verified_tier || "Unassigned"}
                        </span>
                      </div>

                      <p className="mt-3 text-sm text-slate-600">
                        {item.syndrome_match || "Syndrome unavailable"}
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

            {/* Selected patient details */}
            <section className="space-y-4 xl:col-span-2">
              <h2 className="font-semibold text-slate-800">
                Patient Consultation
              </h2>

              {detailsLoading ? (
                <div className="rounded-xl border bg-white p-12 text-center text-slate-500">
                  Loading patient information...
                </div>
              ) : !selectedCase ? (
                <div className="rounded-xl border bg-white p-12 text-center">
                  <Stethoscope
                    size={35}
                    className="mx-auto text-blue-500"
                  />

                  <p className="mt-3 font-semibold text-slate-700">
                    Select a patient
                  </p>

                  <p className="mt-1 text-sm text-slate-500">
                    Choose a case from the doctor queue to view
                    clinical information.
                  </p>
                </div>
              ) : (
                <>
                  {/* Patient overview */}
                  <div className="rounded-xl border bg-white p-6 shadow-sm">
                    <div className="flex flex-wrap items-center justify-between gap-4">
                      <div className="flex items-center gap-3">
                        <div className="rounded-lg bg-blue-50 p-3 text-blue-600">
                          <UserRound size={23} />
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

                      <span
                        className={`rounded-full border px-3 py-1.5 text-sm font-semibold ${tierStyle(
                          selectedCase.human_verified_tier
                        )}`}
                      >
                        {selectedCase.human_verified_tier}
                      </span>
                    </div>

                    <div className="mt-5 grid gap-4 sm:grid-cols-2">
                      <DetailCard
                        title="AI Recommendation"
                        value={selectedCase.ai_triage_tier}
                      />

                      <DetailCard
                        title="Supervisor Verified Tier"
                        value={selectedCase.human_verified_tier}
                      />

                      <DetailCard
                        title="AI Confidence"
                        value={
                          selectedCase.ai_confidence != null
                            ? `${(
                                selectedCase.ai_confidence * 100
                              ).toFixed(1)}%`
                            : null
                        }
                      />

                      <DetailCard
                        title="Five-parameter score"
                        value={
                          selectedCase.vital_assessment
                            ?.five_parameter_score
                        }
                      />
                    </div>

                    {selectedCase.supervisor_comment && (
                      <div className="mt-4 rounded-lg bg-blue-50 p-4">
                        <p className="text-xs font-semibold text-blue-700">
                          Supervisor Review Comment
                        </p>

                        <p className="mt-2 text-sm text-slate-700">
                          {selectedCase.supervisor_comment}
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Vitals */}
                  <div className="rounded-xl border bg-white p-6 shadow-sm">
                    <div className="mb-4 flex items-center gap-2">
                      <Activity
                        size={19}
                        className="text-blue-600"
                      />

                      <h3 className="font-semibold text-slate-800">
                        Patient Vitals
                      </h3>
                    </div>

                    <div className="grid gap-4 sm:grid-cols-3">
                      <DetailCard
                        title="Heart Rate"
                        value={
                          selectedCase.vitals.heart_rate != null
                            ? `${selectedCase.vitals.heart_rate} bpm`
                            : null
                        }
                      />

                      <DetailCard
                        title="Respiratory Rate"
                        value={
                          selectedCase.vitals.resp_rate != null
                            ? `${selectedCase.vitals.resp_rate} /min`
                            : null
                        }
                      />

                      <DetailCard
                        title="Systolic BP"
                        value={
                          selectedCase.vitals.systolic_bp != null
                            ? `${selectedCase.vitals.systolic_bp} mmHg`
                            : null
                        }
                      />

                      <DetailCard
                        title="SpO2"
                        value={
                          selectedCase.vitals.spo2 != null
                            ? `${selectedCase.vitals.spo2}%`
                            : null
                        }
                      />

                      <DetailCard
                        title="Temperature"
                        value={
                          selectedCase.vitals.temperature != null
                            ? `${selectedCase.vitals.temperature} °C`
                            : null
                        }
                      />

                      <DetailCard
                        title="Syndrome Match"
                        value={
                          selectedCase.clinical_analysis.syndrome
                        }
                      />
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

                  {/* SOAP */}
                  <div className="rounded-xl border bg-white p-6 shadow-sm">
                    <div className="mb-4 flex items-center gap-2">
                      <ClipboardList
                        size={19}
                        className="text-purple-600"
                      />

                      <h3 className="font-semibold text-slate-800">
                        AI-Generated SOAP Summary
                      </h3>
                    </div>

                    <div className="space-y-4">
                      {[
                        {
                          title: "Subjective",
                          value: selectedCase.soap.subjective,
                        },
                        {
                          title: "Objective",
                          value: selectedCase.soap.objective,
                        },
                        {
                          title: "Assessment",
                          value: selectedCase.soap.assessment,
                        },
                      ].map((item) => (
                        <div
                          key={item.title}
                          className="rounded-lg bg-slate-50 p-4"
                        >
                          <p className="text-sm font-semibold text-slate-800">
                            {item.title}
                          </p>

                          <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-600">
                            {item.value || "Not available"}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Red flags and missing information */}
                  <div className="grid gap-4 sm:grid-cols-2">
                    <div className="rounded-xl border bg-white p-5 shadow-sm">
                      <div className="mb-3 flex items-center gap-2">
                        <AlertTriangle
                          size={18}
                          className="text-red-500"
                        />

                        <h3 className="font-semibold text-slate-800">
                          Red Flags
                        </h3>
                      </div>

                      {redFlags.length > 0 ? (
                        <div className="flex flex-wrap gap-2">
                          {redFlags.map((flag, index) => (
                            <span
                              key={`${flag}-${index}`}
                              className="rounded-full border border-red-200 bg-red-50 px-3 py-1 text-xs text-red-700"
                            >
                              {flag}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <p className="text-sm text-slate-500">
                          None detected by the prototype.
                        </p>
                      )}
                    </div>

                    <div className="rounded-xl border bg-white p-5 shadow-sm">
                      <div className="mb-3 flex items-center gap-2">
                        <ShieldCheck
                          size={18}
                          className="text-amber-600"
                        />

                        <h3 className="font-semibold text-slate-800">
                          Missing Information
                        </h3>
                      </div>

                      {missingFields.length > 0 ? (
                        <div className="flex flex-wrap gap-2">
                          {missingFields.map((field) => (
                            <span
                              key={field}
                              className="rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-xs text-amber-700"
                            >
                              {field.replaceAll("_", " ")}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <p className="text-sm text-emerald-600">
                          No missing fields detected.
                        </p>
                      )}
                    </div>
                  </div>

                  {/* SHAP */}
                  <div className="rounded-xl border bg-white p-6 shadow-sm">
                    <h3 className="font-semibold text-slate-800">
                      Model Explanation (SHAP)
                    </h3>

                    <pre className="mt-3 max-h-64 overflow-auto rounded-lg bg-slate-50 p-4 text-xs text-slate-700">
                      {JSON.stringify(
                        selectedCase.shap_explanation,
                        null,
                        2
                      ) || "No explanation available"}
                    </pre>

                    <p className="mt-2 text-xs text-slate-400">
                      Model explanations are informational and do not
                      establish clinical causation.
                    </p>
                  </div>

                  {/* Doctor consultation form */}
                  <div className="rounded-xl border border-blue-200 bg-white p-6 shadow-sm">
                    <div className="flex items-center gap-2">
                      <Stethoscope
                        size={20}
                        className="text-blue-600"
                      />

                      <h3 className="text-lg font-semibold text-slate-800">
                        Consultation Record
                      </h3>
                    </div>

                    <p className="mt-1 text-sm text-slate-500">
                      Record the consultation outcome and referral details.
                    </p>

                    <div className="mt-5">
                      <label
                        htmlFor="doctorNotes"
                        className="mb-2 block text-sm font-medium text-slate-700"
                      >
                        Doctor Consultation Notes *
                      </label>

                      <textarea
                        id="doctorNotes"
                        rows={5}
                        value={doctorNotes}
                        onChange={(event) =>
                          setDoctorNotes(event.target.value)
                        }
                        placeholder="Enter consultation findings, examination observations and documented plan..."
                        className="w-full rounded-lg border border-slate-300 px-4 py-3 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                      />
                    </div>

                    <div className="mt-5">
                      <label
                        htmlFor="referralFacility"
                        className="mb-2 block text-sm font-medium text-slate-700"
                      >
                        Referral Facility
                      </label>

                      <div className="relative">
                        <Hospital
                          size={17}
                          className="absolute left-3 top-3.5 text-slate-400"
                        />

                        <input
                          id="referralFacility"
                          type="text"
                          value={referralFacility}
                          onChange={(event) =>
                            setReferralFacility(event.target.value)
                          }
                          placeholder="Enter referral facility, if applicable"
                          className="w-full rounded-lg border border-slate-300 py-3 pl-10 pr-4 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                        />
                      </div>
                    </div>

                    <button
                      onClick={handleComplete}
                      disabled={submitting || !doctorNotes.trim()}
                      className="mt-6 flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 px-5 py-3 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {submitting ? (
                        <>
                          <RefreshCw
                            size={17}
                            className="animate-spin"
                          />
                          Saving consultation...
                        </>
                      ) : (
                        <>
                          <CheckCircle size={17} />
                          Complete Consultation
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
