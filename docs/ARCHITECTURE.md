# Architecture

The Next.js frontend calls a versioned FastAPI API. `ApplicationService` coordinates use cases; the deterministic engines own safety, assessment, training, progression, recovery, and discipline decisions. `SQLiteRepository` owns persistence and can be replaced with a PostgreSQL implementation without moving business rules into SQL.

Local AI is behind `LocalAIService` and is reached only through `OllamaClient`. The pose facade accepts normalized landmarks and returns confidence-aware outputs. Neither AI nor pose code can alter the safety engine directly.

Configuration comes from environment variables. Local SQLite data, raw camera media, model weights, secrets, caches, and temporary outputs are excluded from Git.
