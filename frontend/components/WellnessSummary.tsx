"use client";

import { useEffect, useState } from "react";

import { apiFetch, readUserId } from "../lib/api";
import type { WellnessSummary as WellnessSummaryData } from "../lib/types";

export function WellnessSummary() {
  const [summary, setSummary] = useState<WellnessSummaryData | null>(null);

  useEffect(() => {
    const userId = readUserId();
    if (!userId || userId === "demo") return;
    apiFetch<WellnessSummaryData>(`/api/v1/wellness/summary?user_id=${encodeURIComponent(userId)}`).then(setSummary).catch(() => undefined);
  }, []);

  if (!summary) {
    return <section className="analytics-panel wellness-summary"><p className="eyebrow">Wellness trend</p><h2>Leave a small signal.</h2><p className="stat-caption">Your weight, movement, hydration, and food-awareness trend will appear here after the first local check-in.</p></section>;
  }

  const latestWeight = summary.latest?.body_weight_kg;
  return <section className="analytics-panel wellness-summary"><p className="eyebrow">Wellness trend</p><h2>Small signals, over time.</h2><div className="wellness-stat-row"><span>Latest weight</span><strong>{latestWeight == null ? "—" : `${latestWeight} kg`}</strong></div><div className="wellness-stat-row"><span>Avg movement</span><strong>{summary.averages.daily_movement_minutes == null ? "—" : `${summary.averages.daily_movement_minutes} min`}</strong></div><div className="wellness-stat-row"><span>Avg steps</span><strong>{summary.averages.steps == null ? "—" : Math.round(summary.averages.steps).toLocaleString()}</strong></div><div className="wellness-trend">{summary.body_weight_trend.slice(-5).map((point) => <span key={point.date}>{point.date.slice(5)} · {point.weight_kg}kg</span>)}</div></section>;
}
