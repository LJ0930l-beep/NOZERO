# Testing

Backend checks:

- `python -m pytest -q` covers safety override, goal differentiation, equipment/noise behavior, assessment dimensions, progression, recovery, discipline, API core flow, reassessment, data controls, AI guardrails, and pose uncertainty.
- `python -m ruff check backend ai pose scripts` enforces import, correctness, and style rules.
- `python -m compileall -q backend ai pose scripts` catches syntax errors without network dependencies.

Frontend checks:

- `npm run test` runs the Vitest smoke contract.
- `npx tsc --noEmit` validates strict TypeScript.
- `npm run lint` runs non-interactive ESLint.
- `npm run build` validates the Next production bundle and all routes.
- `npm run e2e` runs Playwright smoke coverage against the production Next server for the Today, Workout, and Onboarding surfaces. Install the browser once with `npx playwright install chromium`.

The remaining test gap is browser-level coverage for camera permissions, responsive layout, and the full API-backed UI workflow. The current smoke tests intentionally use the demo state; the Python MediaPipe adapter has a separate local integration test that skips cleanly when the optional model asset is absent.
