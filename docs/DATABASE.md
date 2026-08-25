# Database

Development uses SQLite with tables for users, exercises, assessments, training cycles, workout sessions, and bounded fitness memory. JSON fields keep catalog and plan structures reviewable while the repository hides SQLite details from engines.

The exercise catalog stores progression/regression metadata, pose rules, and ROM rules. The default file is `backend/data/nozeero.db`; it is ignored by Git. Startup performs only additive schema migration for the local `rom_rules` column, so an existing development database can be upgraded without dropping user data. The `Database` class and repository interface are the migration seam for PostgreSQL. Data-control endpoints expose export, history reset, and user deletion; destructive actions are explicit API calls and are not run by startup.

Assessment history is retained as immutable rows. A reassessment records the new F1–F5 result, computes dimension deltas, and refreshes the active plan from the latest assessment and recent session/recovery signals.
