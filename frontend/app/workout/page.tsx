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
    apiFetch<DailyWorkout>(`/api/v1/workouts/today?user_id=${encodeURIComponent(userId)}`)
      .then((value) => { if (value) setWorkout(value); })
      .catch(() => undefined);
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
          body: JSON.stringify({ user_id: userId, workout_date: workout.date, status: "ZERO", workout_plan: workout, notes: "计划内的 ZERO 日" }),
        });
      } catch (submitError) {
        setError(submitError instanceof Error ? submitError.message : "ZERO 日保存失败。");
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
    const status = doseMode === "full" ? (workout.kind === "RECOVERY" ? "RECOVERY" : "FULL") : "MINIMUM";
    const selectedPlan = {
      ...workout,
      blocks,
      duration_minutes: doseMode === "minimum" ? Math.min(workout.duration_minutes, 6) : doseMode === "short" ? Math.min(workout.duration_minutes, 12) : workout.duration_minutes,
    };
    if (userId && userId !== "demo") {
      try {
        await apiFetch("/api/v1/workouts/feedback", {
          method: "POST",
          body: JSON.stringify({
            user_id: userId,
            workout_date: workout.date,
            status,
            workout_plan: selectedPlan,
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
        setError(submitError instanceof Error ? submitError.message : "反馈保存失败。");
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
            <p className="eyebrow">训练 / {workout.date}</p>
            <h1>{workout.kind === "RECOVERY" ? <><span>主动</span><br /><em>恢复。</em></> : <><span>守住</span><br /><em>承诺。</em></>}</h1>
          </div>
          <div>
            <div className="timer">{String(Math.floor(seconds / 60)).padStart(2, "0")}:{String(seconds % 60).padStart(2, "0")}</div>
            <div className="mode-toggle"><button className={mode === "manual" ? "active" : ""} onClick={() => setMode("manual")}>手动</button><button className={mode === "camera" ? "active" : ""} onClick={() => setMode("camera")}>摄像头</button></div>
          </div>
        </header>
        <div className="workout-layout">
          <section className="workout-list">
            <div className="panel-heading"><div><p className="eyebrow">{workout.focus}</p><h2>{doseMode === "minimum" ? "最小训练" : doseMode === "short" ? "救援训练" : workout.title}</h2></div><span className="state-tag tag-lime">{doseMode === "minimum" ? "6 分钟" : doseMode === "short" ? "12 分钟" : `${workout.duration_minutes} 分钟`}</span></div>
            {mode === "manual" ? <>
              {blocks.length ? blocks.map((block, index) => {
                const completed = completedSets[index] ?? 0;
                return <button className={`workout-block ${activeBlock === index ? "active" : ""} ${completed >= block.sets ? "complete" : ""}`} key={`${block.exercise_id}-${index}`} onClick={() => setActiveBlock(index)} aria-pressed={activeBlock === index}>
                  <span className="block-marker">0{index + 1}</span><span><span className="block-name">{block.name}</span><span className="block-intent">{block.intent}</span><span className="block-progress">{completed}/{block.sets} 组已完成</span></span><span className="block-dose">{block.sets} × {block.reps ?? `${block.duration_seconds} 秒`}</span>
                </button>;
              }) : <div className="empty-state">今天是计划恢复日。可以用计时器做轻量活动，也可以直接记录完成。</div>}
              {blocks.length > 0 && <div className="set-controls"><div className="field-help">当前动作：{activeBlock + 1} / {blocks.length}</div><div className="set-actions"><button className="button button-primary" onClick={markSetComplete}>标记完成一组 ↗</button><button className="button button-secondary" onClick={() => setActiveBlock((current) => Math.max(0, current - 1))}>← 上一个</button><button className="button button-secondary" onClick={nextExercise}>下一个 →</button></div></div>}
            </> : <CameraPanel />}
            <div className="workout-buttons"><button className="button button-primary" onClick={() => setRunning((value) => !value)}>{running ? "暂停计时" : "开始计时"}<span>{running ? "Ⅱ" : "▶"}</span></button><div className="dose-buttons"><button className={`button ${doseMode === "full" ? "button-primary" : "button-secondary"}`} onClick={() => setDoseMode("full")}>完整</button><button className={`button ${doseMode === "short" ? "button-primary" : "button-secondary"}`} onClick={() => setDoseMode("short")}>救援</button><button className={`button ${doseMode === "minimum" ? "button-primary" : "button-secondary"}`} onClick={() => setDoseMode("minimum")}>最小</button></div><button className="button button-secondary" onClick={finishSession} disabled={recorded}>{done ? "填写反馈" : "结束训练"}</button><button className="button button-secondary zero-button" onClick={recordZeroDay} disabled={recorded}>记录 ZERO 日</button></div>
          </section>
          <aside className="camera-card" id="minimum"><p className="eyebrow">信号检查</p><div className="camera-frame"><div><span>{mode === "camera" ? "需要姿态 / 置信度" : "手动模式就绪"}</span><p>{mode === "camera" ? "浏览器画面只在本地预览。当前版本没有宣称自动计数；构图、光线或置信度不足时会显示无法判断。" : "无需摄像头。按自己的节奏计数，保持舒适活动范围，并使用每个动作旁的提示。"}</p></div></div><p className="field-help">原始视频默认不会保存或上传，只有经过计算的结果才可能进入记录。</p></aside>
        </div>
        {done && <section className="feedback-card"><p className="eyebrow">训练已关闭</p><h2>{zeroDay ? "ZERO 日也是一次清晰的选择。" : "很好。现在告诉系统下一次需要知道什么。"}</h2>{!zeroDay && <><div className="form-grid"><div className="field"><label>训练 RPE / {feedback.rpe}</label><input type="range" min="0" max="10" value={feedback.rpe} onChange={(e) => setFeedback({ ...feedback, rpe: Number(e.target.value) })} /></div><div className="field"><label>RIR / {feedback.rir}</label><input type="range" min="0" max="5" value={feedback.rir} onChange={(e) => setFeedback({ ...feedback, rir: Number(e.target.value) })} /></div><div className="field"><label>酸痛 / {feedback.soreness}</label><input type="range" min="0" max="10" value={feedback.soreness} onChange={(e) => setFeedback({ ...feedback, soreness: Number(e.target.value) })} /></div><div className="field"><label>疼痛 / {feedback.pain}</label><input type="range" min="0" max="10" value={feedback.pain} onChange={(e) => setFeedback({ ...feedback, pain: Number(e.target.value) })} /></div><div className="field"><label>疲劳 / {feedback.fatigue}</label><input type="range" min="0" max="10" value={feedback.fatigue} onChange={(e) => setFeedback({ ...feedback, fatigue: Number(e.target.value) })} /></div><div className="field"><label>愉悦度 / {feedback.enjoyment}</label><input type="range" min="0" max="10" value={feedback.enjoyment} onChange={(e) => setFeedback({ ...feedback, enjoyment: Number(e.target.value) })} /></div><div className="field field-wide"><label htmlFor="session-notes">备注</label><textarea id="session-notes" value={feedback.notes} onChange={(e) => setFeedback({ ...feedback, notes: e.target.value })} placeholder="下一次训练需要知道什么？" /></div></div></>}
          <div className="flow-actions"><span className={error ? "error-message" : "field-help"}>{error || (recorded ? `已记录为 ${statusLabel}。恢复可以保护下一次训练。` : "这些数值会影响下一份计划。")}</span>{!recorded && <button className="button button-primary" onClick={recordFeedback}>保存反馈 ↗</button>}</div></section>}
      </div>
    </AppShell>
  );
}
