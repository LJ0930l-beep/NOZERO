# Local AI

The local coach is composed of `OllamaClient`, `PromptRouter`, `ContextBuilder`, `ResponseParser`, `FitnessCoach`, `LocalAIService`, `WeeklyReview`, and `MemoryManager`. Context contains the profile, goal, current plan, recent structured workouts, recovery status, and bounded fitness-memory facts. It does not include an unbounded raw chat transcript. The Ollama request sets `think: false` for Qwen variants that otherwise place the JSON in a hidden thinking field.

The coach may explain, summarize, detect fatigue/time/motivation language, and suggest a shorter path. It cannot diagnose, bypass Safety, increase training after poor recovery, override restrictions, or change deterministic training rules. If Ollama is unavailable or output fails schema validation, a deterministic fallback is returned with `source: fallback`.

The model response is also compared with the deterministic fallback by conservativeness priority (`normal < short < minimum < recovery < stop`). A model response that is less conservative than a safety, pain, fatigue, or dose guardrail is discarded.

Weekly review numbers come from stored sessions; the language model is allowed to write prose around those numbers but not invent them.
