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
  const consistency28 = dashboard.consistency["28"] ?? { completed: 24, planned: 28, percentage: 86 };

  async function askCoach(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!coachPrompt.trim()) return;
    setCoachLoading(true);
    const userId = readUserId();
    try {
      if (!userId || userId === "demo") {
        setCoachResponse({ source: "fallback", fatigue: "unknown", motivation: "moderate", time_available_minutes: null, recommendation: "minimum", reason: "demo mode uses the deterministic local fallback", message: "今天从最小版本开始，保留动作逻辑，不需要把训练做成考试。" });
      } else {
        setCoachResponse(await apiFetch<CoachResponse>("/api/v1/coach", { method: "POST", body: JSON.stringify({ user_id: userId, message: coachPrompt }) }));
      }
    } catch {
      setCoachResponse({ source: "fallback", fatigue: "unknown", motivation: "moderate", time_available_minutes: null, recommendation: "minimum", reason: "the local API was unavailable, so the deterministic fallback was used", message: "本地服务暂时不可用；先做今天计划的最小版本，稍后再同步反馈。" });
    } finally {
      setCoachLoading(false);
    }
  }
  return (
    <AppShell>
      <div className="topbar"><span className="topbar-label">NOZEERO / TRAINING OS</span><span className="topbar-date">{offline ? "LOCAL DEMO MODE" : "SAVED LOCALLY"}</span></div>
      <section className="hero-grid">
        <div className="hero-copy">
          <p className="eyebrow">Wednesday · cycle 04</p>
          <h1>Show up.<br /><em>Stay in.</em></h1>
          <p className="hero-description">A quieter kind of discipline: the right session for today, shaped by your body and your real life.</p>
          <div className="hero-cta-row"><Link href="/workout" className="button button-primary">START TODAY <span>↗</span></Link><Link href="/onboarding" className="text-link">Edit profile</Link></div>
        </div>
        <div className="day-orbit" aria-label={`Day ${workout.day_index + 1}`}>
          <div className="orbit-ring"><div className="orbit-core"><span className="orbit-number">{String(workout.day_index + 1).padStart(2, "0")}</span><span className="orbit-label">DAY</span></div></div>
          <span className="orbit-caption">NO ZERO<br />IS THE PLAN</span>
        </div>
      </section>
      <div className="section-rule"><span>01</span><span>THE SIGNAL</span><span className="rule-line" /></div>
      <section className="metrics-grid">
        <MetricCard label="28-DAY CONSISTENCY" value={`${Math.round(consistency28.percentage)}%`} detail={`${consistency28.completed} of ${consistency28.planned} planned days`} />
        <MetricCard label="CURRENT STREAK" value={`${dashboard.current_streak}d`} detail={`Best: ${dashboard.longest_streak} days`} accent="blue" />
        <MetricCard label="FITNESS / DISCIPLINE" value={`${dashboard.fitness_levels.core ?? "F2"} · ${dashboard.discipline_level.split(" ")[0]}`} detail={`${dashboard.xp.toLocaleString()} XP earned`} accent="orange" />
      </section>
      <div className="content-grid">
        <PlanCard workout={workout} />
        <aside className="coach-card panel">
          <div className="coach-orb"><span>AI</span></div>
          <p className="eyebrow">LOCAL COACH NOTE</p>
          <h2>Keep the floor<br />under the goal.</h2>
          <p className="coach-copy">If energy is low, shrink the session—not the promise. Your minimum workout is already derived from today&apos;s plan.</p>
          <form className="coach-form" onSubmit={askCoach}><input aria-label="Ask local coach" value={coachPrompt} onChange={(event) => setCoachPrompt(event.target.value)} placeholder="今天只有 5 分钟怎么办？" /><button className="button button-secondary" type="submit" disabled={coachLoading}>{coachLoading ? "THINKING…" : "ASK COACH ↗"}</button></form>
          {coachResponse && <div className="coach-result"><span className="state-tag tag-blue">{coachResponse.source.toUpperCase()} / {coachResponse.recommendation.toUpperCase()}</span><p>{coachResponse.message}</p><small>{coachResponse.reason}</small></div>}
          <Link href="/workout#minimum" className="text-link">See minimum version ↗</Link>
        </aside>
      </div>
    </AppShell>
  );
}
