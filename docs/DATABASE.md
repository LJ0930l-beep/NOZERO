# Database

Development uses SQLite with tables for users, exercises, assessments, training cycles, workout sessions, plan executions, progression states, wellness logs, and bounded fitness memory. JSON fields keep catalog and plan structures reviewable while the repository hides SQLite details from engines.

The exercise catalog stores progression/regression metadata, pose rules, and ROM rules. The default file is `backend/data/nozeero.db`; it is ignored by Git. Startup uses `schema_meta` and additive migrations through schema version 2: it adds structured safety flags, the weekly cardio target, progression states, and due-plan execution rows without dropping user data. The `Database` class and repository interface are the migration seam for PostgreSQL. Data-control endpoints expose export, history reset, and user deletion; destructive actions are explicit API calls and are not run by startup.

Assessment history is retained as immutable rows. A reassessment records the new F1–F5 result, computes dimension deltas, and refreshes the active plan from the latest assessment and recent session/recovery signals.

Timestamps are stored in UTC. Workout and plan dates are local calendar dates. Date-window queries are inclusive and use `[reference - (days - 1), reference]`; they never use the last N database rows as a proxy for calendar time.
