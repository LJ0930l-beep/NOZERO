"use client";

import Link from "next/link";
import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";

import { apiFetch, storeUserId } from "../../lib/api";
import { AppShell } from "../../components/AppShell";

type FormState = {
  age: string;
  sex: string;
  height_cm: string;
  weight_kg: string;
  training_experience: string;
  available_training_days: string;
  session_duration_minutes: string;
  available_space: string;
  noise_preference: string;
  jumping_allowed: boolean;
  equipment_mode: string;
  primary_goal: string;
  secondary_focus: string;
  known_medical_restrictions: string;
  recent_injury: string;
  movement_pain: string;
  abnormal_symptoms: string;
  medical_exercise_restriction: string;
};

const initialForm: FormState = {
  age: "30", sex: "prefer_not_to_say", height_cm: "170", weight_kg: "70", training_experience: "beginner",
  available_training_days: "3", session_duration_minutes: "20", available_space: "SMALL", noise_preference: "NORMAL",
  jumping_allowed: true, equipment_mode: "ZERO", primary_goal: "build_exercise_habit", secondary_focus: "full_body",
  known_medical_restrictions: "", recent_injury: "", movement_pain: "", abnormal_symptoms: "", medical_exercise_restriction: "",
};

export default function OnboardingPage() {
  const router = useRouter();
  const [form, setForm] = useState<FormState>(initialForm);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const update = (key: keyof FormState, value: string | boolean) => setForm((current) => ({ ...current, [key]: value }));

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true); setError("");
    try {
      const result = await apiFetch<{ id: string }>("/api/v1/onboarding", {
        method: "POST",
        body: JSON.stringify({
          age: Number(form.age), sex: form.sex, height_cm: Number(form.height_cm), weight_kg: Number(form.weight_kg),
          training_experience: form.training_experience, available_training_days: Number(form.available_training_days),
          session_duration_minutes: Number(form.session_duration_minutes), available_space: form.available_space,
          noise_preference: form.noise_preference, jumping_allowed: form.jumping_allowed, equipment_mode: form.equipment_mode,
          primary_goal: form.primary_goal, secondary_focus: form.secondary_focus,
          safety: {
            known_medical_restrictions: form.known_medical_restrictions, recent_injury: form.recent_injury,
            movement_pain: form.movement_pain, abnormal_symptoms: form.abnormal_symptoms,
            medical_exercise_restriction: form.medical_exercise_restriction,
          },
        }),
      });
      storeUserId(result.id);
      router.push("/assessment");
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Onboarding could not be saved.");
    } finally { setSaving(false); }
  }

  return (
    <AppShell>
      <div className="flow-page">
        <header className="flow-header"><div><p className="eyebrow">Setup / 01</p><h1>Build the<br /><em>baseline.</em></h1></div><p>Tell NOZEERO what your real week looks like. The plan will respect the room, the noise, and your recovery.</p></header>
        <form className="flow-card" onSubmit={submit}>
          <div className="form-grid">
            <div className="field"><label htmlFor="age">Age</label><input id="age" type="number" min="18" max="64" value={form.age} onChange={(e) => update("age", e.target.value)} required /></div>
            <div className="field"><label htmlFor="sex">Sex</label><select id="sex" value={form.sex} onChange={(e) => update("sex", e.target.value)}><option value="prefer_not_to_say">Prefer not to say</option><option value="female">Female</option><option value="male">Male</option><option value="other">Other</option></select></div>
            <div className="field"><label htmlFor="height">Height / cm</label><input id="height" type="number" min="1" value={form.height_cm} onChange={(e) => update("height_cm", e.target.value)} required /></div>
            <div className="field"><label htmlFor="weight">Weight / kg</label><input id="weight" type="number" min="1" value={form.weight_kg} onChange={(e) => update("weight_kg", e.target.value)} required /></div>
            <div className="field"><label htmlFor="experience">Experience</label><select id="experience" value={form.training_experience} onChange={(e) => update("training_experience", e.target.value)}><option value="new">New</option><option value="beginner">Beginner</option><option value="intermediate">Intermediate</option><option value="advanced">Advanced</option></select></div>
            <div className="field"><label htmlFor="days">Training days / week</label><input id="days" type="number" min="1" max="7" value={form.available_training_days} onChange={(e) => update("available_training_days", e.target.value)} required /></div>
            <div className="field"><label htmlFor="duration">Session time / min</label><input id="duration" type="number" min="5" max="180" value={form.session_duration_minutes} onChange={(e) => update("session_duration_minutes", e.target.value)} required /></div>
            <div className="field"><label htmlFor="space">Available space</label><select id="space" value={form.available_space} onChange={(e) => update("available_space", e.target.value)}><option value="SMALL">Small / mat-sized</option><option value="MEDIUM">Medium / floor area</option><option value="LARGE">Large</option></select></div>
            <div className="field field-wide"><label>Equipment mode</label><div className="choice-row">{[["ZERO", "ZERO / bodyweight"], ["HOME", "HOME / common objects"], ["MINIMAL", "MINIMAL / light gear"]].map(([value, label]) => <div className="choice" key={value}><input id={`equipment-${value}`} type="radio" name="equipment" checked={form.equipment_mode === value} onChange={() => update("equipment_mode", value)} /><label htmlFor={`equipment-${value}`}>{label}</label></div>)}</div><span className="field-help">ZERO never assumes a chair or table exists, and does not pretend to cover pulling without an anchor.</span></div>
            <div className="field"><label htmlFor="goal">Primary goal</label><select id="goal" value={form.primary_goal} onChange={(e) => update("primary_goal", e.target.value)}><option value="fat_loss">Fat loss</option><option value="abs">Abs</option><option value="muscle_gain">Muscle gain</option><option value="strength">Strength</option><option value="cardio_fitness">Cardio fitness</option><option value="mobility">Mobility</option><option value="build_exercise_habit">Build exercise habit</option></select></div>
            <div className="field"><label htmlFor="focus">Secondary focus</label><select id="focus" value={form.secondary_focus} onChange={(e) => update("secondary_focus", e.target.value)}><option value="full_body">Full body</option><option value="abs">Abs</option><option value="chest">Chest</option><option value="glutes">Glutes</option><option value="legs">Legs</option><option value="mobility">Mobility</option></select></div>
            <div className="field field-wide"><label htmlFor="noise">Environment</label><div className="choice-row"><div className="choice"><input id="noise-normal" type="radio" name="noise" checked={form.noise_preference === "NORMAL"} onChange={() => update("noise_preference", "NORMAL")} /><label htmlFor="noise-normal">Normal noise</label></div><div className="choice"><input id="noise-quiet" type="radio" name="noise" checked={form.noise_preference === "QUIET"} onChange={() => update("noise_preference", "QUIET")} /><label htmlFor="noise-quiet">Quiet / apartment</label></div><div className="choice"><input id="jumping" type="checkbox" checked={form.jumping_allowed} onChange={(e) => update("jumping_allowed", e.target.checked)} /><label htmlFor="jumping">Jumping allowed</label></div></div></div>
            <div className="field field-wide"><label htmlFor="medical">Safety screening / known restrictions</label><textarea id="medical" placeholder="Leave blank if none. Mention recent injury, movement pain, symptoms, or medical exercise restrictions." value={form.known_medical_restrictions} onChange={(e) => update("known_medical_restrictions", e.target.value)} /></div>
            <div className="field"><label htmlFor="injury">Recent injury</label><input id="injury" value={form.recent_injury} onChange={(e) => update("recent_injury", e.target.value)} placeholder="None" /></div>
            <div className="field"><label htmlFor="pain">Movement pain</label><input id="pain" value={form.movement_pain} onChange={(e) => update("movement_pain", e.target.value)} placeholder="None" /></div>
          </div>
          <div className="flow-actions"><span className={error ? "error-message" : "field-help"}>{error || "For healthy adults 18–64. This is not medical diagnosis or rehabilitation."}</span><button className="button button-primary" type="submit" disabled={saving}>{saving ? "SAVING…" : "SAVE & ASSESS ↗"}</button></div>
        </form>
        <p className="field-help" style={{ marginTop: 18 }}><Link className="text-link" href="/">Back to today</Link></p>
      </div>
    </AppShell>
  );
}
