# Training Engine

`generate_cycle` produces a 28-day cycle of daily records. Each day is either `TRAINING` or planned `RECOVERY`. Goal profiles change schedule, focus order, sets, cardio inclusion, intensity, and dose. User equipment, noise, jumping, space, experience, time, secondary focus, safety status, assessment levels, recent sessions, and recovery status are inputs.

The catalog covers Horizontal Push, Vertical Push, Squat, Lunge, Hip Hinge, Hip Extension, Core Flexion, Anti Extension, Anti Rotation, Lateral Core, Cardio, Mobility, Pull, and the general Core pattern. Exercise selection is deterministic and filtered by equipment, space, noise, impact, structured safety restrictions, contraindications, and jumping restrictions. The LLM never invents a movement or overrides a rule.

Assessment dimensions map to pattern families: upper body to push/pull, lower body to squat/lunge/hinge/extension, core to flexion/anti-extension/anti-rotation/lateral core, cardio to conditioning, and mobility to mobility work. F1–F5 levels cap the selected difficulty; recent high pain/fatigue or a recovery recommendation lowers dose, while a well-tolerated full session permits a conservative next-step increase.

Every training day exposes three plan-derived doses:

- `blocks`: the full session.
- `short_workout`: a three-block rescue dose with reduced sets, duration, and rest.
- `minimum_workout`: the smallest logic-preserving dose, normally two blocks and one set each.

Recovery days expose empty training and rescue lists and remain valid execution outcomes. The frontend records short/minimum execution as `MINIMUM`, so a user can keep the habit without pretending the full plan was completed.

Progression is a separate evidence decision. Reps, sets, tempo, ROM, leverage, unilateral variation, RPE/RIR, form quality, completion, recent load, exposure, frequency, soreness, pain, fatigue, and enjoyment can produce `PROGRESS`, `MAINTAIN`, or `REGRESS`. The latest three matching performances are aggregated into a persisted progression state; two consecutive high-quality or weak performances are required before a lasting change. The engine stores exercise `pose_rules` and `rom_rules` as data so future form checks can be added without changing plan generation.

Training load is calculated from primary set weight 1.0 and secondary set weight 0.5, with separate muscle, movement-pattern, cardio-minute, and total-minute outputs. A high pattern exposure in the recent 48-hour window can remove that pattern from the next plan. Weekly aerobic targets are goal-aware and increase conservatively across the four-week cycle; logged daily movement contributes to the completed dose.
