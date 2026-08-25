# NOZEERO

NOZEERO is a local-first indoor training system for healthy adults aged 18–64. It combines deterministic training rules, safety and recovery gates, a plan-derived minimum workout, local Qwen coaching, manual-first workout execution, and conservative pose-analysis contracts.

The repository name is intentionally `NOZEERO` at `D:\RJ\codex\NOZEERO`. It is a standalone project with its own Git history, dependencies, database, and configuration.

## Current version

`1.0.0-rc.1` — local release candidate. The core onboarding → assessment → 28-day plan → full/short/minimum workout feedback → XP/streak/dashboard/reassessment path is implemented and tested. The Python MediaPipe/OpenCV adapter is locally verified; the browser camera remains preview-only by design until a browser-side model bundle is selected.

## Features

- Onboarding for profile, goals, equipment mode, space, noise, jumping, and safety screening.
- ZERO/HOME/MINIMAL exercise catalog with progression/regression metadata and environment filters.
- Five independent assessment dimensions mapped to F1–F5.
- Rule-based training cycle → daily workout generation with goal-specific frequency, volume, focus, and cardio behavior.
- Movement-pattern coverage across push, pull, squat, lunge, hinge, hip extension, core flexion, anti-extension, anti-rotation, lateral core, cardio, and mobility; assessment levels cap difficulty and recent recovery adjusts dose.
- Progression, recovery, and safety engines independent from the language model.
- FULL, RESCUE/SHORT, MINIMUM, RECOVERY, and ZERO execution states; rescue and minimum sessions are derived from the original plan, and recovery preserves streaks.
- 7/28/90-day consistency, XP, streaks, and separate discipline levels.
- Local Ollama/Qwen boundary with structured output validation and deterministic fallback.
- Manual workout timer and optional local camera preview; raw video is not persisted by default.
- Squat/push-up geometry contracts, calibration checks, confidence states, `UNABLE_TO_DETERMINE` behavior, and an optional local OpenCV/MediaPipe adapter.
- Lightweight nutrition awareness, body-weight trend, hydration/fruit-vegetable reminders, and manual daily-movement logging.
- Dashboard, analytics, reassessment comparison, weekly review, export, history reset, and data deletion endpoints.
- Performance-change and fitness-progress summaries, local discipline achievements, ROM-rule catalog metadata, and assessment-driven plan refresh.

## Architecture

```text
Next.js / React / TypeScript
            │ HTTP JSON
FastAPI application service
   ┌────────┼─────────┐
Safety  Training   Discipline
Recovery Assessment Progression
            │
    SQLite repository seam
            │
 LocalAIService       PoseService
 Ollama/Qwen +        calibration +
 validated fallback   normalized landmarks
```

The business engines are deterministic. AI can interpret language, explain a plan, and suggest a lower-friction option, but it cannot bypass safety, recovery, progression, restrictions, or volume limits.

## Requirements

- Python 3.11+ (tested with Python 3.12)
- Node.js 20+ (tested with Node 24)
- npm
- Git
- Ollama is optional for the core flow and required only for live local-model responses.
- Docker is optional; Docker is not required for the SQLite development path.

## Installation

From the repository root:

```powershell
Copy-Item .env.example .env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev,pose]"
python scripts/seed_data.py
Set-Location frontend
npm ci
Set-Location ..
```

If npm pauses on install scripts, review the pending scripts using the npm version installed on your machine. NOZEERO does not silently enable arbitrary third-party scripts.

## Ollama / Qwen setup

Ollama is not needed for rule-based plan generation. To enable the local coach:

```powershell
ollama serve
ollama pull qwen3.5:9b
```

Set `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, and `OLLAMA_TIMEOUT_SECONDS` in `.env` if your local model tag differs. The default matches the locally available Qwen 9B tag used during smoke verification. If Ollama is unavailable, the API returns a validated deterministic fallback and labels its source as `fallback`.

To require a real local-model response:

```powershell
python scripts/smoke_ollama.py
```

For local Pose inference, download the official model asset after installing the `pose` extra:

```powershell
python scripts/download_pose_model.py
```

## Start backend

From the repository root:

```powershell
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Health check: `GET http://127.0.0.1:8000/api/v1/health`.

## Start frontend

In a second terminal:

```powershell
Set-Location frontend
npm run dev
```

Open `http://localhost:3000`. The UI includes a local demo state so it is inspectable before onboarding; real user data is used after completing onboarding and assessment.

## Database

SQLite is created at `backend/data/nozeero.db` by default and is ignored by Git. Schema initialization is automatic. The repository class keeps persistence details behind a seam for a future PostgreSQL adapter. See [docs/DATABASE.md](docs/DATABASE.md).

## Test and quality commands

```powershell
python -m pytest -q
python -m ruff check backend ai pose scripts
python -m compileall -q backend ai pose scripts
Set-Location frontend
npm run test
npx playwright install chromium
npm run e2e
npx tsc --noEmit
npm run lint
npm run build
```

When Ollama and the configured Qwen model are running, verify the live model separately with `python scripts/smoke_ollama.py`. The regular test command remains runnable without a model and exercises the deterministic fallback.

## Directory structure

```text
NOZEERO/
├── backend/       FastAPI, SQLite repository, domain engines, API tests
├── frontend/      Next.js app, responsive UI, Vitest smoke test
├── ai/            Ollama client, bounded context, schemas, fallback coach
├── pose/          calibration, geometry, counters, form rules
├── data/          exercise catalog and training rules
├── docs/          product, architecture, engine, safety, AI, pose, test, deploy docs
├── scripts/       seed and local development helpers
├── PROJECT_REQUEST.md
├── pyproject.toml
└── docker-compose.yml
```

## Known issues and deferred work

- The API currently has no authentication; it is intended for a local single-user V1 alpha.
- The browser camera route provides permission-safe local preview only. Python-side MediaPipe/OpenCV inference is available through `pose.adapters.mediapipe_adapter`; browser-side frame inference is intentionally deferred so raw video does not cross the local boundary.
- Ollama/Qwen live invocation depends on a locally running model. It was verified in the development environment with `qwen3.5:9b`; an unavailable model falls back deterministically.
- Playwright covers the demo Today, Workout, and Onboarding surfaces. Camera permission, responsive visual QA, and a full API-backed browser journey remain hardware/environment-dependent.
- The GitHub repository is `https://github.com/LJ0930l-beep/NOZERO`; `main` has been uploaded. The final `v1.0.0` tag and GitHub Release are published only after the clean-install acceptance gate.

## Roadmap

1. Add an explicitly opt-in browser-side MediaPipe Tasks bundle and calibration telemetry without uploading frames.
2. Add a local single-user session/auth boundary and richer data export format.
3. Expand Playwright flow coverage and visual QA for mobile workout mode.
4. Add PostgreSQL adapter and migration tooling without changing engine contracts.
5. Publish the verified `v1.0.0` tag and GitHub Release, then continue with browser-side pose inference, auth, and PostgreSQL follow-up work.

See the individual documents in `docs/` for the current contracts.
