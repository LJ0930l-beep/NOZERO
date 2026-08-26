"use client";

import Link from "next/link";
import { useEffect, useState, type FormEvent } from "react";

import { apiFetch, DEMO_DASHBOARD, DEMO_WORKOUT, readUserId } from "../lib/api";
import type { CoachResponse, Dashboard } from "../lib/types";
import { AppShell } from "./AppShell";
import { MetricCard } from "./MetricCard";
import { PlanCard } from "./PlanCard";

export function DashboardScreen() {
  const [dashboard, setDashboard] = useState<Dashboard>(DEMO_DASHBOARD);
  const [offline, setOffline] = useState(false);
  const [coachPrompt, setCoachPrompt] = useState("");
  const [coachResponse, setCoachResponse] = useState<CoachResponse | null>(null);
  const [coachLoading, setCoachLoading] = useState(false);

  useEffect(() => {
    const userId = readUserId();
    if (!userId || userId === "demo") return;
    apiFetch<Dashboard>(`/api/v1/dashboard?user_id=${encodeURIComponent(userId)}`)
      .then(setDashboard)
      .catch(() => setOffline(true));
  }, []);

  const workout = dashboard.next_workout ?? DEMO_WORKOUT;
  const adherence = dashboard.plan_adherence ?? { completed: 24, planned: 28, percentage: 86 };

  async function askCoach(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!coachPrompt.trim()) return;
    setCoachLoading(true);
    const userId = readUserId();
    try {
      if (!userId || userId === "demo") {
        setCoachResponse({
          source: "fallback",
          fatigue: "unknown",
          motivation: "moderate",
          time_available_minutes: null,
          recommendation: "minimum",
          reason: "演示模式使用确定性的本地兜底",
          message: "今天从最小版本开始，保留动作逻辑，不需要把训练做成考试。",
        });
      } else {
        setCoachResponse(await apiFetch<CoachResponse>("/api/v1/coach", {
          method: "POST",
          body: JSON.stringify({ user_id: userId, message: coachPrompt }),
        }));
      }
    } catch {
      setCoachResponse({
        source: "fallback",
        fatigue: "unknown",
        motivation: "moderate",
        time_available_minutes: null,
        recommendation: "minimum",
        reason: "本地 API 暂不可用，已使用确定性兜底",
        message: "本地服务暂时不可用；先做今天计划的最小版本，稍后再同步反馈。",
      });
    } finally {
      setCoachLoading(false);
    }
  }

  return (
    <AppShell>
      <div className="topbar"><span className="topbar-label">NO ZERO / 训练系统</span><span className="topbar-date">{offline ? "本地演示模式" : "已保存到本地"}</span></div>
      <section className="hero-grid">
        <div className="hero-copy">
          <p className="eyebrow">星期三 · 第 04 周期</p>
          <h1>出现。<br /><em>留下。</em></h1>
          <p className="hero-description">一种更安静的自律：让今天的训练适配你的身体，也适配真实生活。</p>
          <div className="hero-cta-row"><Link href="/workout" className="button button-primary">开始今天 <span>↗</span></Link><Link href="/onboarding" className="text-link">编辑档案</Link></div>
        </div>
        <div className="day-orbit" aria-label={`第 ${workout.day_index + 1} 天`}>
          <div className="orbit-ring"><div className="orbit-core"><span className="orbit-number">{String(workout.day_index + 1).padStart(2, "0")}</span><span className="orbit-label">第几天</span></div></div>
          <span className="orbit-caption">NO ZERO<br />就是计划</span>
        </div>
      </section>
      <div className="section-rule"><span>01</span><span>今日信号</span><span className="rule-line" /></div>
      <section className="metrics-grid">
        <MetricCard label="28 天计划执行率" value={`${Math.round(adherence.percentage)}%`} detail={`${adherence.completed} / ${adherence.planned} 个到期计划日`} />
        <MetricCard label="当前连续执行" value={`${dashboard.current_streak} 天`} detail={`历史最佳：${dashboard.longest_streak} 天`} accent="blue" />
        <MetricCard label="体能 / 纪律" value={`${dashboard.fitness_levels.core ?? "F2"} · ${dashboard.discipline_level.split(" ")[0]}`} detail={`已获得 ${dashboard.xp.toLocaleString()} XP`} accent="orange" />
      </section>
      <div className="content-grid">
        <PlanCard workout={workout} />
        <aside className="coach-card panel">
          <div className="coach-orb"><span>AI</span></div>
          <p className="eyebrow">本地教练提示</p>
          <h2>给目标留一块<br />能站住的地面。</h2>
          <p className="coach-copy">如果能量不足，就缩短训练，不要缩短承诺。最小版本已经从今天的计划中生成。</p>
          <form className="coach-form" onSubmit={askCoach}><input aria-label="询问本地教练" value={coachPrompt} onChange={(event) => setCoachPrompt(event.target.value)} placeholder="今天只有 5 分钟怎么办？" /><button className="button button-secondary" type="submit" disabled={coachLoading}>{coachLoading ? "思考中…" : "询问教练 ↗"}</button></form>
          {coachResponse && <div className="coach-result"><span className="state-tag tag-blue">{coachResponse.source === "fallback" ? "本地兜底" : "本地模型"} / {coachResponse.recommendation.toUpperCase()}</span><p>{coachResponse.message}</p><small>{coachResponse.reason}</small></div>}
          <Link href="/workout#minimum" className="text-link">查看最小版本 ↗</Link>
        </aside>
      </div>
    </AppShell>
  );
}
