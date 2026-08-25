"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { apiFetch, DEMO_DASHBOARD, DEMO_WORKOUT, readUserId } from "../lib/api";
import type { Dashboard } from "../lib/types";
import { AppShell } from "./AppShell";
import { MetricCard } from "./MetricCard";
import { PlanCard } from "./PlanCard";

export function DashboardScreen() {
  const [dashboard, setDashboard] = useState<Dashboard>(DEMO_DASHBOARD);
  const [offline, setOffline] = useState(false);

  useEffect(() => {
    const userId = readUserId();
    if (!userId || userId === "demo") return;
    apiFetch<Dashboard>(`/api/v1/dashboard?user_id=${encodeURIComponent(userId)}`)
      .then(setDashboard)
      .catch(() => setOffline(true));
  }, []);

  const workout = dashboard.next_workout ?? DEMO_WORKOUT;
  const consistency28 = dashboard.consistency["28"] ?? { completed: 24, planned: 28, percentage: 86 };
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
          <Link href="/workout#minimum" className="text-link">See minimum version ↗</Link>
        </aside>
      </div>
    </AppShell>
  );
}
