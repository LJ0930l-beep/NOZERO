"use client";

import { useState, type FormEvent } from "react";

import { apiFetch, readUserId } from "../lib/api";

export function WellnessCheckin() {
  const [form, setForm] = useState({ weight: "", steps: "", hydration: "", fruit: "", movement: "", sedentary: "", protein: true });
  const [status, setStatus] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const userId = readUserId();
    if (!userId || userId === "demo") {
      setStatus("Complete onboarding to save a personal wellness log.");
      return;
    }
    try {
      await apiFetch("/api/v1/wellness", {
        method: "POST",
        body: JSON.stringify({
          user_id: userId,
          body_weight_kg: form.weight ? Number(form.weight) : null,
          steps: form.steps ? Number(form.steps) : null,
          hydration_glasses: form.hydration ? Number(form.hydration) : null,
          fruit_vegetable_servings: form.fruit ? Number(form.fruit) : null,
          daily_movement_minutes: form.movement ? Number(form.movement) : null,
          sedentary_minutes: form.sedentary ? Number(form.sedentary) : null,
          protein_awareness: form.protein,
        }),
      });
      setStatus("Wellness log saved locally.");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Wellness log could not be saved.");
    }
  }

  const set = (key: keyof typeof form, value: string | boolean) => setForm((current) => ({ ...current, [key]: value }));
  return (
    <section className="wellness-card panel">
      <div className="panel-heading"><div><p className="eyebrow">Small signals</p><h2>Fuel the session.</h2></div><span className="state-tag tag-blue">OPTIONAL</span></div>
      <p className="coach-copy">Light-touch nutrition and movement awareness. No calorie scanner, no false precision.</p>
      <form className="wellness-grid" onSubmit={submit}>
        <div className="field"><label htmlFor="wellness-weight">Weight / kg</label><input id="wellness-weight" type="number" min="1" step="0.1" value={form.weight} onChange={(event) => set("weight", event.target.value)} placeholder="—" /></div>
        <div className="field"><label htmlFor="wellness-steps">Steps</label><input id="wellness-steps" type="number" min="0" value={form.steps} onChange={(event) => set("steps", event.target.value)} placeholder="—" /></div>
        <div className="field"><label htmlFor="wellness-water">Water / glasses</label><input id="wellness-water" type="number" min="0" value={form.hydration} onChange={(event) => set("hydration", event.target.value)} placeholder="—" /></div>
        <div className="field"><label htmlFor="wellness-plants">Fruit + veg / servings</label><input id="wellness-plants" type="number" min="0" value={form.fruit} onChange={(event) => set("fruit", event.target.value)} placeholder="—" /></div>
        <div className="field"><label htmlFor="wellness-movement">Movement / min</label><input id="wellness-movement" type="number" min="0" value={form.movement} onChange={(event) => set("movement", event.target.value)} placeholder="—" /></div>
        <div className="field"><label htmlFor="wellness-sedentary">Sedentary / min</label><input id="wellness-sedentary" type="number" min="0" value={form.sedentary} onChange={(event) => set("sedentary", event.target.value)} placeholder="—" /></div>
        <label className="wellness-check"><input type="checkbox" checked={form.protein} onChange={(event) => set("protein", event.target.checked)} /> Protein awareness today</label>
        <div className="wellness-submit"><button className="button button-primary" type="submit">SAVE LOG ↗</button><span className="field-help">{status}</span></div>
      </form>
    </section>
  );
}
