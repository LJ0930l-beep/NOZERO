"""Keep durable preferences as small key/value facts instead of chat logs."""

from __future__ import annotations

from typing import Any

ALLOWED_KEYS = {
    "preferred_session_length",
    "favorite_exercises",
    "disliked_exercises",
    "common_skip_time",
    "fatigue_pattern",
    "recovery_pattern",
    "progression_pattern",
    "training_preference",
}


def select_memory_updates(observation: dict[str, Any]) -> dict[str, str]:
    return {key: str(value) for key, value in observation.items() if key in ALLOWED_KEYS and value not in (None, "")}
