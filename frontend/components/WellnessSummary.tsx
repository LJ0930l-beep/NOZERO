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
    return <section className="analytics-panel wellness-summary"><p className="eyebrow">身体状态趋势</p><h2>留下一个小信号。</h2><p className="stat-caption">完成第一次本地记录后，这里会显示体重、活动、饮水和饮食意识趋势。</p></section>;
  }

  const latestWeight = summary.latest?.body_weight_kg;
  return <section className="analytics-panel wellness-summary"><p className="eyebrow">身体状态趋势</p><h2>时间会留下信号。</h2><div className="wellness-stat-row"><span>最新体重</span><strong>{latestWeight == null ? "—" : `${latestWeight} 千克`}</strong></div><div className="wellness-stat-row"><span>平均活动</span><strong>{summary.averages.daily_movement_minutes == null ? "—" : `${summary.averages.daily_movement_minutes} 分钟`}</strong></div><div className="wellness-stat-row"><span>平均步数</span><strong>{summary.averages.steps == null ? "—" : Math.round(summary.averages.steps).toLocaleString()}</strong></div><div className="wellness-trend">{summary.body_weight_trend.slice(-5).map((point) => <span key={point.date}>{point.date.slice(5)} · {point.weight_kg} 千克</span>)}</div></section>;
}
