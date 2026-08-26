# Architecture

The Next.js frontend calls a versioned FastAPI API. `ApplicationService` coordinates use cases; the deterministic engines own safety, restriction resolution, assessment, training load, training, progression, recovery, and discipline decisions. `SQLiteRepository` owns persistence and can be replaced with a PostgreSQL implementation without moving business rules into SQL. `schema_meta` tracks additive migrations for plan executions and progression states.

Local AI is behind `LocalAIService` and is reached only through `OllamaClient`. `PromptRouter`, `ContextBuilder`, `ResponseParser`, `FitnessCoach`, `WeeklyReview`, and `MemoryManager` keep the local-model boundary explicit. The pose facade accepts normalized landmarks and returns confidence-aware outputs; the optional `MediaPipePoseAdapter` converts local OpenCV frames to those landmarks. Neither AI nor pose code can alter the safety engine directly.

Configuration comes from environment variables. Local SQLite data, raw camera media, model weights, secrets, caches, and temporary outputs are excluded from Git.
