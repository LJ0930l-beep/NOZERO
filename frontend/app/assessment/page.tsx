"use client";

import Link from "next/link";
import { useEffect, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";

import { apiFetch, readUserId } from "../../lib/api";
import { AppShell } from "../../components/AppShell";

const tests = [
  ["push_up_reps", "Upper body", "Clean push-up or your safest regression", 0, 40],
  ["squat_reps", "Lower body", "Pain-free bodyweight squats", 0, 70],
  ["plank_seconds", "Core", "Quality plank hold / seconds", 0, 180],
  ["cardio_minutes", "Cardio", "Comfortable low-risk movement / minutes", 0, 90],
  ["mobility_score", "Mobility", "Self-rated comfortable movement / 0–100", 0, 100],
] as const;

export default function AssessmentPage() {
  const router = useRouter();
  const [reassessment, setReassessment] = useState(false);
  const [values, setValues] = useState<Record<string, number>>({ push_up_reps: 5, squat_reps: 15, plank_seconds: 30, cardio_minutes: 10, mobility_score: 50 });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  useEffect(() => { setReassessment(new URLSearchParams(window.location.search).get("mode") === "reassess"); }, []);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const userId = readUserId();
    if (!userId || userId === "demo") { setError("Finish onboarding first to save an assessment."); return; }
    setSaving(true); setError("");
    try {
      await apiFetch(reassessment ? "/api/v1/reassessments" : "/api/v1/assessments", { method: "POST", body: JSON.stringify({ user_id: userId, ...values }) });
      await apiFetch("/api/v1/plans", { method: "POST", body: JSON.stringify({ user_id: userId, cycle_days: 28 }) });
      router.push("/");
    } catch (submitError) { setError(submitError instanceof Error ? submitError.message : "Assessment could not be saved."); }
    finally { setSaving(false); }
  }
  return <AppShell><div className="flow-page"><header className="flow-header"><div><p className="eyebrow">{reassessment ? "Review / 01" : "Setup / 02"}</p><h1>{reassessment ? <>Measure the<br /><em>change.</em></> : <>Find your<br /><em>starting line.</em></>}</h1></div><p>These are not a verdict. They are five independent signals, so the plan can meet your upper body, legs, core, cardio, and mobility where they are.</p></header><form className="flow-card" onSubmit={submit}><div className="score-list">{tests.map(([key, label, help, min, max]) => <div className="score-row" key={key}><div><strong>{label}</strong><small>{help}</small></div><div><input aria-label={label} type="range" min={min} max={max} value={values[key]} onChange={(e) => setValues((current) => ({ ...current, [key]: Number(e.target.value) }))} /><div className="score-number">{values[key]}</div></div></div>)}</div><div className="flow-actions"><span className={error ? "error-message" : "field-help"}>{error || "Stop a test if it creates pain or alarming symptoms."}</span><button className="button button-primary" type="submit" disabled={saving}>{saving ? "UPDATING…" : reassessment ? "UPDATE PLAN ↗" : "BUILD 4-WEEK PLAN ↗"}</button></div></form><p className="field-help" style={{ marginTop: 18 }}><Link className="text-link" href="/onboarding">Back to baseline</Link></p></div></AppShell>;
}
