# Database

Development uses SQLite with tables for users, exercises, assessments, training cycles, workout sessions, and bounded fitness memory. JSON fields keep catalog and plan structures reviewable while the repository hides SQLite details from engines.

The default file is `backend/data/nozeero.db`. It is ignored by Git. The `Database` class and repository interface are the migration seam for PostgreSQL. Data-control endpoints expose export, history reset, and user deletion; destructive actions are explicit API calls and are not run by startup.
