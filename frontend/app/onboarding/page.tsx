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
  exercise_chest_pain: boolean;
  fainting_or_dizziness: boolean;
  unusual_shortness_of_breath: boolean;
};

const initialForm: FormState = {
  age: "30", sex: "prefer_not_to_say", height_cm: "170", weight_kg: "70", training_experience: "beginner",
  available_training_days: "3", session_duration_minutes: "20", available_space: "SMALL", noise_preference: "NORMAL",
  jumping_allowed: true, equipment_mode: "ZERO", primary_goal: "build_exercise_habit", secondary_focus: "full_body",
  known_medical_restrictions: "", recent_injury: "", movement_pain: "", abnormal_symptoms: "", medical_exercise_restriction: "",
  exercise_chest_pain: false, fainting_or_dizziness: false, unusual_shortness_of_breath: false,
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
      const result = await apiFetch<{ id: string; safety_result?: { status: string; blockers?: string[] } }>("/api/v1/onboarding", {
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
            exercise_chest_pain: form.exercise_chest_pain, fainting_or_dizziness: form.fainting_or_dizziness,
            unusual_shortness_of_breath: form.unusual_shortness_of_breath,
          },
        }),
      });
      if (result.safety_result?.status === "BLOCKED") {
        setError(`安全筛查已阻止训练计划：${result.safety_result.blockers?.join("、") || "请先获得专业建议"}。`);
        return;
      }
      storeUserId(result.id);
      router.push("/assessment");
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "资料保存失败。");
    } finally { setSaving(false); }
  }

  return (
    <AppShell>
      <div className="flow-page">
        <header className="flow-header"><div><p className="eyebrow">设置 / 01</p><h1>建立你的<br /><em>基线。</em></h1></div><p>告诉 NO ZERO 真实的一周是什么样子。计划会尊重你的空间、噪音和恢复状态。</p></header>
        <form className="flow-card" onSubmit={submit}>
          <div className="form-grid">
            <div className="field"><label htmlFor="age">年龄</label><input id="age" type="number" min="18" max="64" value={form.age} onChange={(e) => update("age", e.target.value)} required /></div>
            <div className="field"><label htmlFor="sex">性别</label><select id="sex" value={form.sex} onChange={(e) => update("sex", e.target.value)}><option value="prefer_not_to_say">不便透露</option><option value="female">女性</option><option value="male">男性</option><option value="other">其他</option></select></div>
            <div className="field"><label htmlFor="height">身高 / 厘米</label><input id="height" type="number" min="1" value={form.height_cm} onChange={(e) => update("height_cm", e.target.value)} required /></div>
            <div className="field"><label htmlFor="weight">体重 / 千克</label><input id="weight" type="number" min="1" value={form.weight_kg} onChange={(e) => update("weight_kg", e.target.value)} required /></div>
            <div className="field"><label htmlFor="experience">训练经验</label><select id="experience" value={form.training_experience} onChange={(e) => update("training_experience", e.target.value)}><option value="new">刚开始</option><option value="beginner">初学</option><option value="intermediate">中级</option><option value="advanced">进阶</option></select></div>
            <div className="field"><label htmlFor="days">每周训练天数</label><input id="days" type="number" min="1" max="7" value={form.available_training_days} onChange={(e) => update("available_training_days", e.target.value)} required /></div>
            <div className="field"><label htmlFor="duration">单次时长 / 分钟</label><input id="duration" type="number" min="5" max="180" value={form.session_duration_minutes} onChange={(e) => update("session_duration_minutes", e.target.value)} required /></div>
            <div className="field"><label htmlFor="space">可用空间</label><select id="space" value={form.available_space} onChange={(e) => update("available_space", e.target.value)}><option value="SMALL">小 / 瑜伽垫大小</option><option value="MEDIUM">中 / 一块地面</option><option value="LARGE">大</option></select></div>
            <div className="field field-wide"><label>器械模式</label><div className="choice-row">{[["ZERO", "ZERO / 自重"], ["HOME", "HOME / 常见物品"], ["MINIMAL", "MINIMAL / 轻器械"]].map(([value, label]) => <div className="choice" key={value}><input id={`equipment-${value}`} type="radio" name="equipment" checked={form.equipment_mode === value} onChange={() => update("equipment_mode", value)} /><label htmlFor={`equipment-${value}`}>{label}</label></div>)}</div><span className="field-help">ZERO 不假设你有椅子或桌子，也不会假装没有锚点就能安全完成拉类动作。</span></div>
            <div className="field"><label htmlFor="goal">主要目标</label><select id="goal" value={form.primary_goal} onChange={(e) => update("primary_goal", e.target.value)}><option value="fat_loss">减脂</option><option value="abs">腹部</option><option value="muscle_gain">增肌</option><option value="body_shaping">塑形</option><option value="strength">力量</option><option value="cardio_fitness">心肺</option><option value="core_strength">核心力量</option><option value="mobility">灵活性</option><option value="build_exercise_habit">建立运动习惯</option></select></div>
            <div className="field"><label htmlFor="focus">次要关注</label><select id="focus" value={form.secondary_focus} onChange={(e) => update("secondary_focus", e.target.value)}><option value="full_body">全身</option><option value="abs">腹部</option><option value="chest">胸部</option><option value="back">背部</option><option value="shoulders">肩部</option><option value="arms">手臂</option><option value="glutes">臀部</option><option value="legs">腿部</option><option value="mobility">灵活性</option></select></div>
            <div className="field field-wide"><label htmlFor="noise">环境</label><div className="choice-row"><div className="choice"><input id="noise-normal" type="radio" name="noise" checked={form.noise_preference === "NORMAL"} onChange={() => update("noise_preference", "NORMAL")} /><label htmlFor="noise-normal">普通噪音</label></div><div className="choice"><input id="noise-quiet" type="radio" name="noise" checked={form.noise_preference === "QUIET"} onChange={() => update("noise_preference", "QUIET")} /><label htmlFor="noise-quiet">安静 / 公寓</label></div><div className="choice"><input id="jumping" type="checkbox" checked={form.jumping_allowed} onChange={(e) => update("jumping_allowed", e.target.checked)} /><label htmlFor="jumping">允许跳跃</label></div></div></div>
            <div className="field field-wide"><label>结构化安全筛查</label><div className="choice-row"><div className="choice"><input id="chest-pain" type="checkbox" checked={form.exercise_chest_pain} onChange={(e) => update("exercise_chest_pain", e.target.checked)} /><label htmlFor="chest-pain">运动时胸痛</label></div><div className="choice"><input id="fainting" type="checkbox" checked={form.fainting_or_dizziness} onChange={(e) => update("fainting_or_dizziness", e.target.checked)} /><label htmlFor="fainting">晕厥或头晕</label></div><div className="choice"><input id="breath" type="checkbox" checked={form.unusual_shortness_of_breath} onChange={(e) => update("unusual_shortness_of_breath", e.target.checked)} /><label htmlFor="breath">异常气短</label></div></div><span className="field-help">勾选任意红旗项后，系统会停止普通训练计划并提示寻求专业建议。</span></div>
            <div className="field field-wide"><label htmlFor="medical">已知限制或补充说明</label><textarea id="medical" placeholder="没有就留空；可填写近期受伤、动作疼痛、症状或医生建议。" value={form.known_medical_restrictions} onChange={(e) => update("known_medical_restrictions", e.target.value)} /></div>
            <div className="field"><label htmlFor="injury">近期受伤</label><input id="injury" value={form.recent_injury} onChange={(e) => update("recent_injury", e.target.value)} placeholder="无" /></div>
            <div className="field"><label htmlFor="pain">动作疼痛</label><input id="pain" value={form.movement_pain} onChange={(e) => update("movement_pain", e.target.value)} placeholder="无" /></div>
            <div className="field field-wide"><label htmlFor="symptoms">其他异常症状</label><input id="symptoms" value={form.abnormal_symptoms} onChange={(e) => update("abnormal_symptoms", e.target.value)} placeholder="无" /></div>
          </div>
          <div className="flow-actions"><span className={error ? "error-message" : "field-help"}>{error || "适用于 18–64 岁健康成年人；不是医疗诊断或康复工具。"}</span><button className="button button-primary" type="submit" disabled={saving}>{saving ? "保存中…" : "保存并评估 ↗"}</button></div>
        </form>
        <p className="field-help" style={{ marginTop: 18 }}><Link className="text-link" href="/">返回今日</Link></p>
      </div>
    </AppShell>
  );
}
