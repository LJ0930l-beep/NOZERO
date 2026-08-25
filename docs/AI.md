# Local AI

The local coach is composed of a client, bounded context builder, structured response parser, coach service, and memory manager. Context contains the profile, goal, current plan, recent structured workouts, recovery status, consistency, and bounded fitness-memory facts. It does not include an unbounded raw chat transcript.

The coach may explain, summarize, detect fatigue/time/motivation language, and suggest a shorter path. It cannot diagnose, bypass Safety, increase training after poor recovery, override restrictions, or change deterministic training rules. If Ollama is unavailable or output fails schema validation, a deterministic fallback is returned with `source: fallback`.

Weekly review numbers come from stored sessions; the language model is allowed to write prose around those numbers but not invent them.
