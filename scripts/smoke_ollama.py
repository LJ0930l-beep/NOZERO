"""Run a real local Qwen structured-output smoke test.

This intentionally fails if the model is unavailable or the service falls back;
unit tests cover the fallback separately.
"""

from __future__ import annotations

import os

from ai.ollama.client import OllamaClient
from ai.ollama.service import LocalAIService


def main() -> None:
    client = OllamaClient(
        os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
        os.getenv("OLLAMA_MODEL", "qwen3.5:9b"),
        float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "60")),
    )
    service = LocalAIService(client, allow_model=True)
    source, decision = service.coach(
        "我今天只有6分钟，而且很累，给我一个安全的建议。",
        {
            "age": 30,
            "training_experience": "beginner",
            "available_training_days": 3,
            "session_duration_minutes": 20,
            "equipment_mode": "ZERO",
            "noise_preference": "QUIET",
            "jumping_allowed": False,
            "primary_goal": "build_exercise_habit",
            "secondary_focus": "full_body",
        },
        {"title": "Low-friction habit", "duration_minutes": 20},
        [],
        "NORMAL",
        {},
        "SAFE",
    )
    if source != "ollama":
        raise SystemExit(f"Ollama smoke did not use the local model: {decision.model_dump()}")
    print({"source": source, "decision": decision.model_dump()})


if __name__ == "__main__":
    main()
