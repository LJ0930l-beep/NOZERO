# Deployment

The documented local path runs FastAPI with SQLite and Next.js with the API base URL configured through `NEXT_PUBLIC_API_BASE_URL`. `docker-compose.yml` provides an optional two-container path; Docker is not required for development.

Before a release, run all commands in `scripts/test_all.ps1`, review `.gitignore`, verify that no `.env`, database, media, model weights, or user data is tracked, and perform a clean clone/install/database-init smoke test. Ollama should be treated as a local optional dependency and its model tag should be recorded in the release notes.

External GitHub repository creation, pushing, and release tagging require explicit account authorization and are intentionally separate from local file generation.
