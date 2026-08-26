"use client";

import Link from "next/link";
import { useEffect, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";

import { apiFetch, readUserId } from "../../lib/api";
import { AppShell } from "../../components/AppShell";

const tests = [
  ["push_up_reps", "上肢", "标准俯卧撑，或你最安全的退阶动作", 0, 40],
  ["squat_reps", "下肢", "无痛自重深蹲次数", 0, 70],
  ["plank_seconds", "核心", "保持高质量平板支撑 / 秒", 0, 180],
  ["cardio_minutes", "心肺", "舒适、低风险的活动 / 分钟", 0, 90],
  ["mobility_score", "灵活性", "自评舒适活动能力 / 0–100", 0, 100],
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
    if (!userId || userId === "demo") { setError("请先完成基础资料，才能保存评估。"); return; }
    setSaving(true); setError("");
    try {
      await apiFetch(reassessment ? "/api/v1/reassessments" : "/api/v1/assessments", { method: "POST", body: JSON.stringify({ user_id: userId, ...values }) });
      if (!reassessment) {
        await apiFetch("/api/v1/plans", { method: "POST", body: JSON.stringify({ user_id: userId, cycle_days: 28 }) });
      }
      router.push("/");
    } catch (submitError) { setError(submitError instanceof Error ? submitError.message : "评估保存失败。"); }
    finally { setSaving(false); }
  }
  return <AppShell><div className="flow-page"><header className="flow-header"><div><p className="eyebrow">{reassessment ? "复评 / 01" : "设置 / 02"}</p><h1>{reassessment ? <>测量你的<br /><em>变化。</em></> : <>找到你的<br /><em>起点。</em></>}</h1></div><p>这不是评判，而是五个彼此独立的信号，让计划从你的上肢、下肢、核心、心肺和灵活性真实水平开始。</p></header><form className="flow-card" onSubmit={submit}><div className="score-list">{tests.map(([key, label, help, min, max]) => <div className="score-row" key={key}><div><strong>{label}</strong><small>{help}</small></div><div><input aria-label={label} type="range" min={min} max={max} value={values[key]} onChange={(e) => setValues((current) => ({ ...current, [key]: Number(e.target.value) }))} /><div className="score-number">{values[key]}</div></div></div>)}</div><p className="field-help">F1–F5 是内部训练放置标签，不是医疗评级。</p><div className="flow-actions"><span className={error ? "error-message" : "field-help"}>{error || "如果产生疼痛或警示症状，请立即停止测试。"}</span><button className="button button-primary" type="submit" disabled={saving}>{saving ? "更新中…" : reassessment ? "更新计划 ↗" : "生成四周计划 ↗"}</button></div></form><p className="field-help" style={{ marginTop: 18 }}><Link className="text-link" href="/onboarding">返回基线</Link></p></div></AppShell>;
}
