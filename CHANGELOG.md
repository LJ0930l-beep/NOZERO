# Changelog

## 1.0.0 — 2026-08-26

### Released

- Published tag `v1.0.0` and GitHub Release at `https://github.com/LJ0930l-beep/NOZERO/releases/tag/v1.0.0`.
- Accepted after local and fresh-clone quality gates; see `docs/PHASE-12-REPORT.md`.

## 1.0.0-rc.1 — 2026-08-26

### Added

- Plan-derived SHORT/RESCUE and MINIMUM workout doses with explicit frontend dose selection.
- Movement-pattern coverage and assessment/history/recovery-aware exercise difficulty and volume selection.
- Reassessment-driven plan refresh, performance-change and fitness-progress summaries, weekly-review recommendations, and local discipline achievements.
- Exercise ROM-rule metadata with additive SQLite migration and pose calibration edge-case coverage.

### Verified

- Backend/AI/pose tests, Ruff, compileall, frontend Vitest, TypeScript, ESLint, Next build, and Playwright smoke are the release-candidate gates; final clean-install evidence is recorded in the Phase 12 report.

## 1.0.0-alpha.1 — 2026-08-26

### Added

- Full primary-goal and secondary-focus coverage, equipment-limited Pull exercises, local wellness logs, weight trend, and daily-movement summaries.
- Explicit PromptRouter, ContextBuilder, ResponseParser, FitnessCoach, WeeklyReview, and MemoryManager boundaries.
- Local Qwen smoke helper, optional MediaPipe/OpenCV Tasks adapter, Playwright E2E smoke tests, and conservative AI guardrail tests.
- Manual workout set tracking, RIR/fatigue/notes feedback, and explicit ZERO-day logging.
- Reassessment UI entry point and plan refresh flow.

### Verified

- Backend, AI, pose, and frontend quality gates pass locally; see `docs/PHASE-12-REPORT.md`.

## 1.0.0-alpha.0 — 2026-08-26

### Added

- Standalone NOZEERO repository and project contract.
- FastAPI backend, SQLite schema/repository, health endpoint, configuration, and structured error boundary.
- Onboarding, safety screening, exercise seed catalog, assessment, training cycle, feedback, dashboard, weekly review, reassessment, and data-control endpoints.
- Deterministic training, progression, recovery, discipline, pose, and local-AI fallback modules.
- Next.js responsive interface for Today, Onboarding, Assessment, Workout, and Analytics.
- Python, AI, pose, and frontend smoke tests.

### Changed

- None; this is the initial alpha.

### Fixed

- None; this is the initial alpha.

### Known Issues

- Browser MediaPipe capture and GitHub release automation remain deferred; see README.
