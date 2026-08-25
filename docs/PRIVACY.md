# Privacy and security review

## Local-first defaults

- The development database is SQLite under `backend/data/` and is ignored by Git.
- Raw camera video is not written by the frontend or backend contract. The camera route is a permission-safe local preview; derived pose results are the only data eligible for persistence.
- Ollama requests are directed to the configured local base URL. External AI is disabled by default in `.env.example`.
- Export, reset-history, and delete-data endpoints are available for the single local user boundary.

## Review checklist

- No tracked `.env`, database, model weights, raw video, cache, test-results, or temporary artifacts.
- Request schemas bound numeric ranges, notes length, age, and supported goal/equipment values.
- Safety screening and plan blocking are deterministic and independent of the language model.
- The frontend stores only a local user id in `localStorage`; it does not upload camera frames.

## Known boundary

This V1 alpha is a local single-user application and has no authentication or multi-user authorization layer. Do not expose the development API to an untrusted network. Add an auth/session boundary before any shared deployment.
