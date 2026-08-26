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
      setStatus("请先完成基础资料，才能保存个人记录。");
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
      setStatus("身体状态已保存到本地。");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "身体状态保存失败。");
    }
  }

  const set = (key: keyof typeof form, value: string | boolean) => setForm((current) => ({ ...current, [key]: value }));
  return (
    <section className="wellness-card panel">
      <div className="panel-heading"><div><p className="eyebrow">小信号</p><h2>为训练补充信息。</h2></div><span className="state-tag tag-blue">可选</span></div>
      <p className="coach-copy">轻量记录营养和活动意识。不扫描卡路里，也不制造虚假的精确。</p>
      <form className="wellness-grid" onSubmit={submit}>
        <div className="field"><label htmlFor="wellness-weight">体重 / 千克</label><input id="wellness-weight" type="number" min="1" step="0.1" value={form.weight} onChange={(event) => set("weight", event.target.value)} placeholder="—" /></div>
        <div className="field"><label htmlFor="wellness-steps">步数</label><input id="wellness-steps" type="number" min="0" value={form.steps} onChange={(event) => set("steps", event.target.value)} placeholder="—" /></div>
        <div className="field"><label htmlFor="wellness-water">饮水 / 杯</label><input id="wellness-water" type="number" min="0" value={form.hydration} onChange={(event) => set("hydration", event.target.value)} placeholder="—" /></div>
        <div className="field"><label htmlFor="wellness-plants">果蔬 / 份</label><input id="wellness-plants" type="number" min="0" value={form.fruit} onChange={(event) => set("fruit", event.target.value)} placeholder="—" /></div>
        <div className="field"><label htmlFor="wellness-movement">日常活动 / 分钟</label><input id="wellness-movement" type="number" min="0" value={form.movement} onChange={(event) => set("movement", event.target.value)} placeholder="—" /></div>
        <div className="field"><label htmlFor="wellness-sedentary">久坐 / 分钟</label><input id="wellness-sedentary" type="number" min="0" value={form.sedentary} onChange={(event) => set("sedentary", event.target.value)} placeholder="—" /></div>
        <label className="wellness-check"><input type="checkbox" checked={form.protein} onChange={(event) => set("protein", event.target.checked)} /> 今天有蛋白质意识</label>
        <div className="wellness-submit"><button className="button button-primary" type="submit">保存记录 ↗</button><span className="field-help">{status}</span></div>
      </form>
    </section>
  );
}
