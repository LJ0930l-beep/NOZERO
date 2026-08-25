# NOZEERO V1 Project Contract

## Product

NOZEERO is a local-first indoor training system for healthy adults aged 18–64. Its principle is: users may train less, but they should not train blindly; recovery is a valid planned outcome; rules and safety outrank AI suggestions; and the system must acknowledge equipment and pose-estimation limits.

This repository is intentionally independent from every other project under `D:/RJ/codex`, including `ai-market-analyst`. Do not copy its source tree, database, configuration, or runtime artifacts into this repository.

## Required architecture

- Frontend: Next.js, React, TypeScript, responsive desktop-first UI with a mobile-friendly camera workout route. Tailwind or a similarly maintainable component approach is acceptable.
- Backend: Python FastAPI with clear API, service, engine, repository, schema, and model boundaries.
- Database: SQLite for development through an ORM or repository abstraction that can later target PostgreSQL.
- Local AI: Ollama with Qwen 9B behind `LocalAIService`, `OllamaClient`, `PromptRouter`, `ContextBuilder`, `ResponseParser`, `FitnessCoach`, `WeeklyReview`, and `MemoryManager`. AI must never own safety or training-rule decisions.
- Pose: modular camera calibration, pose detection, exercise classification, rep counting, form analysis, and confidence management. Manual mode must work without a camera.
- Tests: backend unit/integration tests, frontend tests, end-to-end coverage, AI guardrail tests, training-engine tests, and pose edge-case tests where the runtime permits.

## V1 capabilities

1. Onboarding: profile, goals, equipment (`ZERO`, `HOME`, `MINIMAL`), space, noise/jumping constraints, and safety screening.
2. Structured exercise database with movement pattern, muscles, difficulty, equipment, space/noise/impact, ranges, sets, RPE/RIR, progression/regression, contraindications, pose support, rules, cues, and review metadata.
3. Multidimensional assessment: upper body, lower body, core, cardio, and mobility, each mapped to F1–F5 with history.
4. Rule-based scientific training engine: training cycle → weekly plan → daily workout; goal differentiation, movement balance, available time, equipment, environment, and restrictions must change the result.
5. Progression/regression engine using completion, reps, sets, tempo, ROM, leverage, unilateral variation, RPE/RIR, form quality, and recovery; output `PROGRESS`, `MAINTAIN`, or `REGRESS`.
6. Recovery engine outputting `NORMAL`, `REDUCED`, `RECOVERY`, or `SWAP_FOCUS` using RPE, RIR, soreness, pain, fatigue, enjoyment, recent load, exposure, and frequency.
7. Safety engine independent of the LLM. Red-flag symptoms such as chest pain, fainting, severe breathing difficulty, serious exercise-related discomfort, acute injury, or medical restriction must stop normal workout generation and recommend professional advice.
8. Discipline engine with FULL, MINIMUM, RECOVERY, and ZERO day states; minimum and rescue workouts must derive from the original plan; recovery days preserve streaks; consistency windows are 7/28/90 days; XP and discipline level are distinct from fitness level.
9. Local AI coach with structured context, validated JSON, retry/fallback, weekly review, and bounded structured fitness memory. It may explain and suggest but cannot bypass safety, recovery, progression, restrictions, or volume limits.
10. Workout experience with timer, manual reps, sets, rest, progress, next exercise, optional camera mode, and post-session RPE/RIR/soreness/pain/fatigue/enjoyment/notes.
11. Pose foundation with calibration checks, confidence states `GOOD`, `POTENTIAL_ISSUE`, and `UNABLE_TO_DETERMINE`; prioritize reliable squat and push-up counting and never claim certainty when camera conditions are inadequate.
12. Dashboard, training statistics, streak, consistency, XP/levels, assessment comparisons, scheduled reassessment every 2–4 weeks, and lightweight nutrition/daily-movement support.
13. Local privacy defaults: raw camera video is not saved or uploaded by default; only derived results and statistics are persisted. Provide data export, delete, and reset-history seams.

## Explicit V1 exclusions

No community, leaderboard, social feed, medical diagnosis, rehabilitation prescription, child/elderly/pregnancy specialization, complete nutrition database, food-photo calorie system, complex subscriptions, cloud video storage, advanced wearable dependency, or broad 50+ pose catalog.

## Delivery phases

Work in order and verify after each phase:

- Phase 0: repository, frontend, backend, database, configuration, logging, error handling, health endpoint, test foundation, environment example, ignore rules, and docs skeleton.
- Phase 1: onboarding, goals, equipment/environment, quiet mode, safety screening.
- Phase 2: exercise schema, seed data, progression/regression trees, and filtering.
- Phase 3: assessment dimensions, fitness levels, and history.
- Phase 4: cycle/weekly/daily scientific training generation.
- Phase 5: progression, recovery, and safety validation.
- Phase 6: discipline, minimum/rescue, recovery days, streak, consistency, XP, and levels.
- Phase 7: local Qwen/Ollama integration, structured context/output, coach, weekly review, memory.
- Phase 8: manual-first workout UI, timer, rest, progress, and feedback.
- Phase 9: camera calibration, MediaPipe integration seam, squat/push-up counters, confidence, and form feedback.
- Phase 10: analytics dashboard.
- Phase 11: reassessment and plan updates.
- Phase 12: end-to-end integration from new user through onboarding, assessment, four-week plan, workout, feedback, XP/streak, AI explanation, dashboard, and reassessment.

## Acceptance

The project is not complete until the implemented core flow is runnable, tested, documented, and clean-installable from this repository. Run build, lint, typecheck, and tests where applicable. The final report must disclose implementation status, test status, known issues, deferred work, privacy/security review, sensitive-file review, and clean-install verification. Do not claim Qwen or camera functionality passed unless the real local dependency and fallback behavior have been verified.

## Working rules

- Keep business rules deterministic and testable; never replace them with free-form LLM generation.
- Safety outranks streaks; recovery counts as planned execution; consistency is not erased by one missed day.
- Keep modules low-coupled and configuration centralized.
- Prefer a reversible local implementation when optional hardware or model dependencies are absent.
- Use meaningful commits after verified phases and never commit secrets, real user data, model weights, raw video, local production databases, caches, or temporary artifacts.
