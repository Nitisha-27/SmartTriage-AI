
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  User,
  Activity,
  FileText,
  Send,
  ArrowLeft,
  AlertTriangle,
  CheckCircle,
  Loader2,
} from "lucide-react";

import api from "@/lib/api";
import Sidebar from "@/components/Sidebar";
import Header from "@/components/Header";

interface AssessmentResult {
  case_id?: number;
  status?: string;
  ai_triage_tier?: string;
  ai_confidence?: number;
  syndrome_match?: string;
  syndrome_similarity?: number;
  detected_red_flags?: string[];
  missing_fields?: string[];
  shap_explanation?: unknown;
  [key: string]: unknown;
}

export default function PatientIntake() {
  const router = useRouter();

  const [form, setForm] = useState({
    patient_name: "",
    age: "",
    gender: "Female",
    raw_narrative: "",
    heart_rate: "",
    resp_rate: "",
    systolic_bp: "",
    spo2: "",
    temperature: "",
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<AssessmentResult | null>(null);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setResult(null);

    const numericFields = [
      "age",
      "heart_rate",
      "resp_rate",
      "systolic_bp",
      "spo2",
      "temperature",
    ] as const;

    for (const field of numericFields) {
      if (form[field].trim() === "") {
        setError(`Please enter ${field.replaceAll("_", " ")}.`);
        return;
      }
    }

    setLoading(true);

    const payload = {
      patient_name: form.patient_name.trim(),
      age: Number(form.age),
      gender: form.gender,
      raw_narrative: form.raw_narrative.trim(),
      vitals: {
        heart_rate: Number(form.heart_rate),
        resp_rate: Number(form.resp_rate),
        systolic_bp: Number(form.systolic_bp),
        spo2: Number(form.spo2),
        temperature: Number(form.temperature),
      },
    };

    try {
      const response = await api.post("/cases/intake", payload);
const data = response.data;

const assessment = data.assessment ?? {};
const clinical = assessment.clinical_analysis ?? {};
const ml = assessment.ml_assessment ?? {};

setResult({
  case_id: data.case_id,
  status: data.status,

  ai_triage_tier: ml.triage_tier ?? null,
  ai_confidence: ml.confidence ?? null,

  syndrome_match: clinical.syndrome ?? null,
  syndrome_similarity: clinical.syndrome_similarity ?? null,

  detected_red_flags: clinical.red_flags ?? [],
  missing_fields: clinical.missing_fields ?? [],

  shap_explanation: assessment.shap_explanation ?? [],

  clinical_analysis: clinical,
  vital_assessment: assessment.vital_assessment ?? {},
  ml_assessment: ml,
});
    } catch (err: unknown) {
      console.error("Patient intake error:", err);

      const message =
        typeof err === "object" &&
        err !== null &&
        "response" in err
          ? (err as { response?: { data?: { detail?: string } } })
              .response?.data?.detail
          : undefined;

      setError(
        typeof message === "string"
          ? message
          : "Unable to submit patient assessment. Please check the backend connection."
      );
    } finally {
      setLoading(false);
    }
  };

  const inputClass =
    "mt-2 w-full rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-800 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100";

  return (
    <div className="min-h-screen bg-slate-50">
      <Sidebar />

      <main className="ml-64 min-h-screen">
        <Header />

        <div className="space-y-6 p-8">
          <div>
            <button
              onClick={() => router.push("/")}
              className="mb-4 flex items-center gap-2 text-sm text-slate-500 hover:text-blue-600"
            >
              <ArrowLeft size={16} />
              Back to Dashboard
            </button>

            <h1 className="text-2xl font-bold text-slate-800">
              Patient Intake
            </h1>

            <p className="mt-1 text-sm text-slate-500">
              Register a patient and submit clinical information for
              prototype assessment.
            </p>
          </div>

          {error && (
            <div className="flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              <AlertTriangle size={18} />
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Patient Information */}

            <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="mb-6 flex items-center gap-3">
                <div className="rounded-lg bg-blue-50 p-2 text-blue-600">
                  <User size={21} />
                </div>

                <div>
                  <h2 className="font-semibold text-slate-800">
                    Patient Information
                  </h2>
                  <p className="text-xs text-slate-500">
                    Basic patient details
                  </p>
                </div>
              </div>

              <div className="grid gap-5 md:grid-cols-3">
                <div>
                  <label className="text-sm font-medium text-slate-700">
                    Patient Name *
                  </label>
                  <input
                    name="patient_name"
                    value={form.patient_name}
                    onChange={handleChange}
                    placeholder="Enter patient name"
                    className={inputClass}
                    required
                  />
                </div>

                <div>
                  <label className="text-sm font-medium text-slate-700">
                    Age *
                  </label>
                  <input
                    name="age"
                    type="number"
                    min="0"
                    max="120"
                    value={form.age}
                    onChange={handleChange}
                    placeholder="Enter age"
                    className={inputClass}
                    required
                  />
                </div>

                <div>
                  <label className="text-sm font-medium text-slate-700">
                    Gender *
                  </label>
                  <select
                    name="gender"
                    value={form.gender}
                    onChange={handleChange}
                    className={inputClass}
                  >
                    <option>Female</option>
                    <option>Male</option>
                    <option>Other</option>
                  </select>
                </div>
              </div>
            </section>

            {/* Clinical Narrative */}

            <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="mb-6 flex items-center gap-3">
                <div className="rounded-lg bg-purple-50 p-2 text-purple-600">
                  <FileText size={21} />
                </div>

                <div>
                  <h2 className="font-semibold text-slate-800">
                    Clinical Information
                  </h2>
                  <p className="text-xs text-slate-500">
                    Describe the patient's symptoms and medical history
                  </p>
                </div>
              </div>

              <label className="text-sm font-medium text-slate-700">
                Patient Clinical Narrative *
              </label>

              <textarea
                name="raw_narrative"
                value={form.raw_narrative}
                onChange={handleChange}
                rows={6}
                placeholder="Describe symptoms, duration, pain severity, medical history, allergies, medications and onset..."
                className={inputClass}
                required
              />

              <p className="mt-2 text-xs text-slate-400">
                Include as much relevant clinical information as available.
              </p>
            </section>

            {/* Vital Signs */}

            <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="mb-6 flex items-center gap-3">
                <div className="rounded-lg bg-emerald-50 p-2 text-emerald-600">
                  <Activity size={21} />
                </div>

                <div>
                  <h2 className="font-semibold text-slate-800">
                    Vital Signs
                  </h2>
                  <p className="text-xs text-slate-500">
                    Enter the patient's measured vital parameters
                  </p>
                </div>
              </div>

              <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
                <div>
                  <label className="text-sm font-medium text-slate-700">
                    Heart Rate (bpm) *
                  </label>
                  <input
                    name="heart_rate"
                    type="number"
                    min="1"
                    value={form.heart_rate}
                    onChange={handleChange}
                    placeholder="e.g. 85"
                    className={inputClass}
                    required
                  />
                </div>

                <div>
                  <label className="text-sm font-medium text-slate-700">
                    Respiratory Rate (/min) *
                  </label>
                  <input
                    name="resp_rate"
                    type="number"
                    min="1"
                    value={form.resp_rate}
                    onChange={handleChange}
                    placeholder="e.g. 18"
                    className={inputClass}
                    required
                  />
                </div>

                <div>
                  <label className="text-sm font-medium text-slate-700">
                    Systolic BP (mmHg) *
                  </label>
                  <input
                    name="systolic_bp"
                    type="number"
                    min="1"
                    value={form.systolic_bp}
                    onChange={handleChange}
                    placeholder="e.g. 120"
                    className={inputClass}
                    required
                  />
                </div>

                <div>
                  <label className="text-sm font-medium text-slate-700">
                    Oxygen Saturation (%) *
                  </label>
                  <input
                    name="spo2"
                    type="number"
                    min="1"
                    max="100"
                    value={form.spo2}
                    onChange={handleChange}
                    placeholder="e.g. 98"
                    className={inputClass}
                    required
                  />
                </div>

                <div>
                  <label className="text-sm font-medium text-slate-700">
                    Temperature (°C) *
                  </label>
                  <input
                    name="temperature"
                    type="number"
                    step="0.1"
                    value={form.temperature}
                    onChange={handleChange}
                    placeholder="e.g. 37.0"
                    className={inputClass}
                    required
                  />
                </div>
              </div>
            </section>

            <div className="flex justify-end">
              <button
                type="submit"
                disabled={loading}
                className="flex items-center gap-2 rounded-lg bg-blue-600 px-6 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {loading ? (
                  <>
                    <Loader2 size={17} className="animate-spin" />
                    Processing Assessment...
                  </>
                ) : (
                  <>
                    <Send size={17} />
                    Submit Patient Assessment
                  </>
                )}
              </button>
            </div>
          </form>

          {/* Assessment Result */}

          {result && (
            <section className="rounded-xl border border-emerald-200 bg-white p-6 shadow-sm">
              <div className="mb-5 flex items-center gap-3">
                <CheckCircle className="text-emerald-600" size={24} />
                <div>
                  <h2 className="font-semibold text-slate-800">
                    Assessment Submitted
                  </h2>
                  <p className="text-sm text-slate-500">
                    Case #{String(result.case_id ?? "Created")}
                  </p>
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="rounded-lg bg-slate-50 p-4">
                  <p className="text-xs text-slate-500">AI Triage Tier</p>
                  <p className="mt-1 text-lg font-bold text-slate-800">
                    {String(result.ai_triage_tier ?? "Not available")}
                  </p>
                </div>

                <div className="rounded-lg bg-slate-50 p-4">
                  <p className="text-xs text-slate-500">Case Status</p>
                  <p className="mt-1 text-lg font-bold text-slate-800">
                    {String(result.status ?? "Submitted")}
                  </p>
                </div>

                <div className="rounded-lg bg-slate-50 p-4">
                  <p className="text-xs text-slate-500">Syndrome Match</p>
                  <p className="mt-1 font-semibold text-slate-800">
                    {String(result.syndrome_match ?? "Not available")}
                  </p>
                </div>

                <div className="rounded-lg bg-slate-50 p-4">
                  <p className="text-xs text-slate-500">AI Confidence</p>
                  <p className="mt-1 font-semibold text-slate-800">
                    {result.ai_confidence == null
                      ? "Not available"
                      : `${(Number(result.ai_confidence) * 100).toFixed(1)}%`}
                  </p>
                </div>
              </div>

              {Array.isArray(result.detected_red_flags) &&
                result.detected_red_flags.length > 0 && (
                  <div className="mt-5 rounded-lg border border-red-200 bg-red-50 p-4">
                    <p className="mb-2 text-sm font-semibold text-red-700">
                      Detected Red Flags
                    </p>
                    <ul className="list-inside list-disc text-sm text-red-700">
                      {result.detected_red_flags.map((flag, index) => (
                        <li key={index}>{String(flag)}</li>
                      ))}
                    </ul>
                  </div>
                )}

              {Array.isArray(result.missing_fields) &&
                result.missing_fields.length > 0 && (
                  <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-4">
                    <p className="mb-2 text-sm font-semibold text-amber-700">
                      Missing Clinical Information
                    </p>
                    <ul className="list-inside list-disc text-sm text-amber-700">
                      {result.missing_fields.map((field, index) => (
                        <li key={index}>{String(field)}</li>
                      ))}
                    </ul>
                  </div>
                )}

              <p className="mt-5 text-xs text-slate-400">
                Educational prototype only. AI-generated assessments are not
                clinically validated and must not be used to make real patient
                care decisions.
              </p>
            </section>
          )}
        </div>
      </main>
    </div>
  );
}
