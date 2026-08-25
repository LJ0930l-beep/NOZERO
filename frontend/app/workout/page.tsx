"use client";

import { useEffect, useMemo, useState } from "react";

import { AppShell } from "../../components/AppShell";
import { CameraPanel } from "../../components/CameraPanel";
import { apiFetch, DEMO_WORKOUT, readUserId } from "../../lib/api";
import type { DailyWorkout } from "../../lib/types";

type Feedback = { rpe: number; rir: number; soreness: number; pain: number; fatigue: number; enjoyment: number; notes: string };
type DoseMode = "full" | "short" | "minimum";

export default function WorkoutPage() {
  const [workout, setWorkout] = useState<DailyWorkout>(DEMO_WORKOUT);
  const [doseMode, setDoseMode] = useState<DoseMode>("full");
  const [mode, setMode] = useState<"manual" | "camera">("manual");
  const [seconds, setSeconds] = useState(0);
  const [running, setRunning] = useState(false);
  const [done, setDone] = useState(false);
  const [recorded, setRecorded] = useState(false);
  const [zeroDay, setZeroDay] = useState(false);
  const [activeBlock, setActiveBlock] = useState(0);
  const [completedSets, setCompletedSets] = useState<Record<number, number>>({});
  const [error, setError] = useState("");
  const [feedback, setFeedback] = useState<Feedback>({ rpe: 7, rir: 2, soreness: 2, pain: 0, fatigue: 3, enjoyment: 7, notes: "" });
  const blocks = useMemo(() => {
    if (doseMode === "minimum") return workout.minimum_workout;
    if (doseMode === "short") return workout.short_workout;
    return workout.blocks;
  }, [doseMode, workout]);

  useEffect(() => {
    setActiveBlock(0);
    setCompletedSets({});
  }, [doseMode, workout]);

  useEffect(() => {
    const userId = readUserId();
    if (!userId || userId === "demo") return;
    apiFetch<DailyWorkout>(`/api/v1/workouts/today?user_id=${encodeURIComponent(userId)}`).then((value) => { if (value) setWorkout(value); }).catch(() => undefined);
  }, []);

  useEffect(() => {
    if (!running) return;
    const timer = window.setInterval(() => setSeconds((value) => value + 1), 1000);
    return () => window.clearInterval(timer);
  }, [running]);

  function finishSession() {
    setRunning(false);
    setDone(true);
    setError("");
  }

  function markSetComplete() {
    const block = blocks[activeBlock];
    if (!block) return;
    setCompletedSets((current) => ({ ...current, [activeBlock]: Math.min(block.sets, (current[activeBlock] ?? 0) + 1) }));
  }

  function nextExercise() {
    if (!blocks.length) return;
    setActiveBlock((current) => Math.min(blocks.length - 1, current + 1));
  }

  async function recordZeroDay() {
    const userId = readUserId();
    if (userId && userId !== "demo") {
      try {
        await apiFetch("/api/v1/workouts/feedback", {
          method: "POST",
          body: JSON.stringify({ user_id: userId, workout_date: workout.date, status: "ZERO", workout_plan: workout, notes: "planned zero day" }),
        });
      } catch (submitError) {
        setError(submitError instanceof Error ? submitError.message : "Zero day could not be saved.");
        return;
      }
    }
    setZeroDay(true);
    setDone(true);
    setRecorded(true);
    setError("");
  }

  async function recordFeedback() {
    const userId = readUserId();
    if (userId && userId !== "demo") {
      try {
        await apiFetch("/api/v1/workouts/feedback", {
          method: "POST",
          body: JSON.stringify({
            user_id: userId,
            workout_date: workout.date,
            status: doseMode === "full" ? (workout.kind === "RECOVERY" ? "RECOVERY" : "FULL") : "MINIMUM",
            workout_plan: workout,
            session_rpe: feedback.rpe,
            rir: feedback.rir,
            soreness: feedback.soreness,
            pain: feedback.pain,
            fatigue: feedback.fatigue,
            enjoyment: feedback.enjoyment,
            notes: feedback.notes,
          }),
        });
      } catch (submitError) {
        setError(submitError instanceof Error ? submitError.message : "Feedback could not be saved.");
        return;
      }
    }
    setRecorded(true);
    setError("");
  }

  const statusLabel = zeroDay ? "ZERO" : doseMode === "short" ? "SHORT / MINIMUM" : doseMode === "minimum" ? "MINIMUM" : workout.kind === "RECOVERY" ? "RECOVERY" : "FULL";
  return (
    <AppShell>
      <div className="workout-page">
        <header className="workout-header">
          <div>
            <p className="eyebrow">Session / {workout.date}</p>
            <h1>{workout.kind === "RECOVERY" ? <><span>Recover</span><br /><em>on purpose.</em></> : <><span>Keep the</span><br /><em>promise.</em></>}</h1>
          </div>
          <div>
            <div className="timer">{String(Math.floor(seconds / 60)).padStart(2, "0")}:{String(seconds % 60).padStart(2, "0")}</div>
            <div className="mode-toggle"><button className={mode === "manual" ? "active" : ""} onClick={() => setMode("manual")}>MANUAL</button><button className={mode === "camera" ? "active" : ""} onClick={() => setMode("camera")}>CAMERA</button></div>
          </div>
        </header>
        <div className="workout-layout">
          <section className="workout-list">
            <div className="panel-heading"><div><p className="eyebrow">{workout.focus}</p><h2>{doseMode === "minimum" ? "Minimum workout" : doseMode === "short" ? "Rescue workout" : workout.title}</h2></div><span className="state-tag tag-lime">{doseMode === "minimum" ? "6 MIN" : doseMode === "short" ? "12 MIN" : `${workout.duration_minutes} MIN`}</span></div>
            {mode === "manual" ? <>
              {blocks.length ? blocks.map((block, index) => {
                const completed = completedSets[index] ?? 0;
                return <button className={`workout-block ${activeBlock === index ? "active" : ""} ${completed >= block.sets ? "complete" : ""}`} key={`${block.exercise_id}-${index}`} onClick={() => setActiveBlock(index)} aria-pressed={activeBlock === index}>
                  <span className="block-marker">0{index + 1}</span><span><span className="block-name">{block.name}</span><span className="block-intent">{block.intent}</span><span className="block-progress">{completed}/{block.sets} sets complete</span></span><span className="block-dose">{block.sets} × {block.reps ?? `${block.duration_seconds}s`}</span>
                </button>;
              }) : <div className="empty-state">Planned recovery. Use the timer for a gentle reset, or log the day as complete.</div>}
              {blocks.length > 0 && <div className="set-controls"><div className="field-help">Current block: {activeBlock + 1} / {blocks.length}</div><div className="set-actions"><button className="button button-primary" onClick={markSetComplete}>MARK SET COMPLETE ↗</button><button className="button button-secondary" onClick={() => setActiveBlock((current) => Math.max(0, current - 1))}>← PREVIOUS</button><button className="button button-secondary" onClick={nextExercise}>NEXT EXERCISE →</button></div></div>}
            </> : <CameraPanel />}
            <div className="workout-buttons"><button className="button button-primary" onClick={() => setRunning((value) => !value)}>{running ? "PAUSE TIMER" : "START TIMER"}<span>{running ? "Ⅱ" : "▶"}</span></button><div className="dose-buttons"><button className={`button ${doseMode === "full" ? "button-primary" : "button-secondary"}`} onClick={() => setDoseMode("full")}>FULL</button><button className={`button ${doseMode === "short" ? "button-primary" : "button-secondary"}`} onClick={() => setDoseMode("short")}>RESCUE</button><button className={`button ${doseMode === "minimum" ? "button-primary" : "button-secondary"}`} onClick={() => setDoseMode("minimum")}>MINIMUM</button></div><button className="button button-secondary" onClick={finishSession} disabled={recorded}>{done ? "FEEDBACK BELOW" : "FINISH SESSION"}</button><button className="button button-secondary zero-button" onClick={recordZeroDay} disabled={recorded}>LOG ZERO DAY</button></div>
          </section>
          <aside className="camera-card" id="minimum"><p className="eyebrow">Signal check</p><div className="camera-frame"><div><span>{mode === "camera" ? "POSE / CONFIDENCE REQUIRED" : "MANUAL MODE READY"}</span><p>{mode === "camera" ? "The browser preview is local only. If framing, lighting, or confidence is not enough, NOZEERO will say unable to determine." : "No camera required. Count your reps, keep the range comfortable, and use the cues beside each block."}</p></div></div><p className="field-help">Raw video is not saved or uploaded by default. Only the derived result is eligible for storage.</p></aside>
        </div>
        {done && <section className="feedback-card"><p className="eyebrow">Session closed</p><h2>{zeroDay ? "A zero day is still a visible choice." : "Good. Now tell the system what it should learn."}</h2>{!zeroDay && <><div className="form-grid"><div className="field"><label>Session RPE / {feedback.rpe}</label><input type="range" min="0" max="10" value={feedback.rpe} onChange={(e) => setFeedback({ ...feedback, rpe: Number(e.target.value) })} /></div><div className="field"><label>RIR / {feedback.rir}</label><input type="range" min="0" max="5" value={feedback.rir} onChange={(e) => setFeedback({ ...feedback, rir: Number(e.target.value) })} /></div><div className="field"><label>Soreness / {feedback.soreness}</label><input type="range" min="0" max="10" value={feedback.soreness} onChange={(e) => setFeedback({ ...feedback, soreness: Number(e.target.value) })} /></div><div className="field"><label>Pain / {feedback.pain}</label><input type="range" min="0" max="10" value={feedback.pain} onChange={(e) => setFeedback({ ...feedback, pain: Number(e.target.value) })} /></div><div className="field"><label>Fatigue / {feedback.fatigue}</label><input type="range" min="0" max="10" value={feedback.fatigue} onChange={(e) => setFeedback({ ...feedback, fatigue: Number(e.target.value) })} /></div><div className="field"><label>Enjoyment / {feedback.enjoyment}</label><input type="range" min="0" max="10" value={feedback.enjoyment} onChange={(e) => setFeedback({ ...feedback, enjoyment: Number(e.target.value) })} /></div><div className="field field-wide"><label htmlFor="session-notes">Notes</label><textarea id="session-notes" value={feedback.notes} onChange={(e) => setFeedback({ ...feedback, notes: e.target.value })} placeholder="What should the next session know?" /></div></div></>}
          <div className="flow-actions"><span className={error ? "error-message" : "field-help"}>{error || (recorded ? `Recorded as ${statusLabel}. Recovery can protect the next session.` : "These values influence the next plan.")}</span>{!recorded && <button className="button button-primary" onClick={recordFeedback}>SAVE FEEDBACK ↗</button>}</div></section>}
      </div>
    </AppShell>
  );
}
