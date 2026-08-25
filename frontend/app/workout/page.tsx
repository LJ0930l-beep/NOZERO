"use client";

import { useEffect, useMemo, useState } from "react";
import { apiFetch, DEMO_WORKOUT, readUserId } from "../../lib/api";
import type { DailyWorkout } from "../../lib/types";
import { AppShell } from "../../components/AppShell";

export default function WorkoutPage() {
  const [workout, setWorkout] = useState<DailyWorkout>(DEMO_WORKOUT);
  const [minimum, setMinimum] = useState(false);
  const [mode, setMode] = useState<"manual" | "camera">("manual");
  const [seconds, setSeconds] = useState(0);
  const [running, setRunning] = useState(false);
  const [done, setDone] = useState(false);
  const [feedback, setFeedback] = useState({ rpe: 7, soreness: 2, pain: 0, fatigue: 3, enjoyment: 7 });
  const blocks = useMemo(() => minimum ? workout.minimum_workout : workout.blocks, [minimum, workout]);
  useEffect(() => {
    const userId = readUserId();
    if (!userId || userId === "demo") return;
    apiFetch<DailyWorkout>(`/api/v1/workouts/today?user_id=${encodeURIComponent(userId)}`).then((value) => { if (value) setWorkout(value); }).catch(() => undefined);
  }, []);
  useEffect(() => { if (!running) return; const timer = window.setInterval(() => setSeconds((value) => value + 1), 1000); return () => window.clearInterval(timer); }, [running]);
  async function complete() {
    const userId = readUserId();
    if (userId && userId !== "demo") {
      await apiFetch("/api/v1/workouts/feedback", { method: "POST", body: JSON.stringify({ user_id: userId, workout_date: workout.date, status: minimum ? "MINIMUM" : workout.kind === "RECOVERY" ? "RECOVERY" : "FULL", workout_plan: workout, session_rpe: feedback.rpe, soreness: feedback.soreness, pain: feedback.pain, fatigue: feedback.fatigue, enjoyment: feedback.enjoyment, notes: "" }) }).catch(() => undefined);
    }
    setRunning(false); setDone(true);
  }
  return <AppShell><div className="workout-page"><header className="workout-header"><div><p className="eyebrow">Session / {workout.date}</p><h1>{workout.kind === "RECOVERY" ? "Recover<br /><em>on purpose.</em>" : "Keep the<br /><em>promise.</em>"}</h1></div><div><div className="timer">{String(Math.floor(seconds / 60)).padStart(2, "0")}:{String(seconds % 60).padStart(2, "0")}</div><div className="mode-toggle"><button className={mode === "manual" ? "active" : ""} onClick={() => setMode("manual")}>MANUAL</button><button className={mode === "camera" ? "active" : ""} onClick={() => setMode("camera")}>CAMERA</button></div></div></header><div className="workout-layout"><section className="workout-list"><div className="panel-heading"><div><p className="eyebrow">{workout.focus}</p><h2>{minimum ? "Minimum workout" : workout.title}</h2></div><span className="state-tag tag-lime">{minimum ? "6 MIN" : `${workout.duration_minutes} MIN`}</span></div>{mode === "manual" ? blocks.map((block, index) => <div className="workout-block" key={`${block.exercise_id}-${index}`}><span className="block-marker">0{index + 1}</span><div><div className="block-name">{block.name}</div><div className="block-intent">{block.intent}</div></div><span className="block-dose">{block.sets} × {block.reps ?? `${block.duration_seconds}s`}</span></div>) : <div className="camera-frame" style={{ marginTop: 25 }}><div><span>CAMERA CALIBRATION</span><p>Frame your full body, keep the camera still, and use Manual Mode if confidence is not GOOD.</p></div></div>}<div className="workout-buttons"><button className="button button-primary" onClick={() => setRunning((value) => !value)}>{running ? "PAUSE TIMER" : "START TIMER"}<span>{running ? "Ⅱ" : "▶"}</span></button><button className="button button-secondary" onClick={() => setMinimum((value) => !value)}>{minimum ? "USE FULL PLAN" : "SWITCH TO MINIMUM"}</button><button className="button button-secondary" onClick={complete}>{done ? "COMPLETED" : "FINISH SESSION"}</button></div></section><aside className="camera-card" id="minimum"><p className="eyebrow">Signal check</p><div className="camera-frame"><div><span>{mode === "camera" ? "POSE / NOT YET VERIFIED" : "MANUAL MODE READY"}</span><p>{mode === "camera" ? "The camera is optional. If framing, lighting, or confidence is not enough, NOZEERO will say unable to determine." : "No camera required. Count your reps, keep the range comfortable, and use the cues beside each block."}</p></div></div><p className="field-help">Raw video is not saved or uploaded by default. Only the derived result is eligible for storage.</p></aside></div>{done && <section className="feedback-card"><p className="eyebrow">Session closed</p><h2>Good. Now tell the system what it should learn.</h2><div className="form-grid"><div className="field"><label>Session RPE / {feedback.rpe}</label><input type="range" min="0" max="10" value={feedback.rpe} onChange={(e) => setFeedback({ ...feedback, rpe: Number(e.target.value) })} /></div><div className="field"><label>Soreness / {feedback.soreness}</label><input type="range" min="0" max="10" value={feedback.soreness} onChange={(e) => setFeedback({ ...feedback, soreness: Number(e.target.value) })} /></div><div className="field"><label>Pain / {feedback.pain}</label><input type="range" min="0" max="10" value={feedback.pain} onChange={(e) => setFeedback({ ...feedback, pain: Number(e.target.value) })} /></div><div className="field"><label>Enjoyment / {feedback.enjoyment}</label><input type="range" min="0" max="10" value={feedback.enjoyment} onChange={(e) => setFeedback({ ...feedback, enjoyment: Number(e.target.value) })} /></div></div><p className="success-message" style={{ marginTop: 22 }}>Result recorded as {minimum ? "MINIMUM" : workout.kind === "RECOVERY" ? "RECOVERY" : "FULL"}. Recovery can protect the next session.</p></section>}</div></AppShell>;
}
