# Testing

Backend checks:

- `python -m pytest -q` covers safety override, structured restrictions, actual-date windows, muscle/pattern load, due-plan adherence, persisted progression, goal differentiation, equipment/noise behavior, assessment dimensions, recovery, discipline, API core flow, reassessment-driven plan refresh, data controls, AI guardrails, migration compatibility, and pose uncertainty.
- `python -m ruff check backend ai pose scripts` enforces import, correctness, and style rules.
- `python -m compileall -q backend ai pose scripts` catches syntax errors without network dependencies.

Frontend checks:

- `npm run test` runs the Vitest smoke contract.
- `npx tsc --noEmit` validates strict TypeScript.
- `npm run lint` runs non-interactive ESLint.
- `npm run build` validates the Next production bundle and all routes.
- `npm run e2e` runs Playwright smoke coverage plus `full-user-flow.spec.ts`, `safety-block.spec.ts`, and `minimum-workout.spec.ts` against the production Next server. Install the browser once with `npx playwright install chromium`.

The remaining test gap is real browser-side pose inference because rc2 explicitly downgrades the camera surface to local preview. The Python MediaPipe adapter has a separate local integration test that skips cleanly when the optional model asset is absent. A clean-install run must repeat the Python and frontend gates from a fresh checkout without the local database, Ollama state, pose model, or dependency caches.
