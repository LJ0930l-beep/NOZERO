# NO ZERO Evidence Registry

This registry separates external guidance, conservative product choices, and internal UX rules. A source listed here is not presented as an original NO ZERO rule.

| rule_id | description | source | source_version | date | evidence_type | implemented_in | reviewed_at |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SAFETY-RED-FLAG | Chest pain, fainting/dizziness, and unusual shortness of breath stop normal training | NO ZERO acceptance task | v1-acceptance | 2026-08-27 | conservative product choice | `backend/app/engines/safety/engine.py` | 2026-08-27 |
| SAFETY-RESTRICTION | Contraindication tags exclude a movement; restriction tags select a regression or lower dose | NO ZERO acceptance task | v1-acceptance | 2026-08-27 | internal deterministic rule | `backend/app/engines/safety/restrictions.py`, `backend/app/engines/training/engine.py` | 2026-08-27 |
| WINDOW-INCLUSIVE | A seven-day window is `[local_today - 6 days, local_today]` | NO ZERO acceptance task | v1-acceptance | 2026-08-27 | internal data contract | `backend/app/engines/time_windows.py` | 2026-08-27 |
| LOAD-SETS | Primary set weight is 1.0 and secondary set weight is 0.5 | NO ZERO acceptance task | v1-acceptance | 2026-08-27 | conservative product choice | `backend/app/engines/training/load.py` | 2026-08-27 |
| ADHERENCE-DUE | Plan adherence uses successful execution of due plan days; planned recovery is successful | NO ZERO acceptance task | v1-acceptance | 2026-08-27 | internal deterministic rule | `backend/app/engines/discipline/engine.py`, `backend/app/services/application.py` | 2026-08-27 |
| CARDIO-DOSE | Weekly aerobic target increases with cardio-oriented goals and gradually across four weeks | NO ZERO acceptance task | v1-acceptance | 2026-08-27 | conservative product choice | `backend/app/engines/training/load.py`, `backend/app/engines/training/engine.py` | 2026-08-27 |
| POSE-PRIVACY | Raw camera video stays local; unsupported or low-confidence pose is not counted | NO ZERO pose contract | v1 | 2026-08-27 | privacy/internal UX rule | `frontend/components/CameraPanel.tsx`, `pose/` | 2026-08-27 |
