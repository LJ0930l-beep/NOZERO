import Link from "next/link";
import type { DailyWorkout } from "../lib/types";

export function PlanCard({ workout }: { workout: DailyWorkout }) {
  const isRecovery = workout.kind === "RECOVERY";
  return (
    <section className="plan-card panel">
      <div className="panel-heading">
        <div>
        <p className="eyebrow">今日 / {workout.date}</p>
          <h2>{workout.title}</h2>
        </div>
        <span className={`state-tag ${isRecovery ? "tag-blue" : "tag-lime"}`}>{isRecovery ? "RECOVERY" : `${workout.duration_minutes} MIN`}</span>
      </div>
      <div className="plan-focus"><span className="focus-line" />{workout.focus}</div>
      {isRecovery ? (
        <div className="recovery-note"><span>↺</span><div><strong>恢复也是训练。</strong><p>按计划恢复，今天不会中断你的执行记录。</p></div></div>
      ) : (
        <div className="exercise-list">
          {workout.blocks.map((block, index) => (
            <div className="exercise-row" key={`${block.exercise_id}-${index}`}>
              <span className="exercise-index">0{index + 1}</span>
              <span className="exercise-name">{block.name}</span>
              <span className="exercise-dose">{block.sets} × {block.reps ?? `${block.duration_seconds}s`}</span>
            </div>
          ))}
        </div>
      )}
      <div className="plan-actions">
        <Link href="/workout" className="button button-primary">{isRecovery ? "打开恢复日" : "开始训练"}<span>↗</span></Link>
        {!isRecovery && <span className="minimum-note">最小版本已准备 · 6 分钟</span>}
      </div>
    </section>
  );
}
