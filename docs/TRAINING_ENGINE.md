# Training Engine

`generate_cycle` produces a cycle of daily records. Each day is either `TRAINING` or planned `RECOVERY`. Goal profiles change schedule, focus order, sets, cardio inclusion, intensity, and minimum-workout size. User equipment, noise, jumping, space, experience, time, and safety status are inputs.

The engine selects from a structured exercise catalog. It does not ask the LLM to invent a workout. `build_minimum_workout` takes the first logic-preserving blocks from the daily plan, reduces sets/reps/duration, and marks them as minimum work.

Progression is a separate evidence decision: completion, RPE/RIR, form quality, recovery, and difficulty produce `PROGRESS`, `MAINTAIN`, or `REGRESS`.
