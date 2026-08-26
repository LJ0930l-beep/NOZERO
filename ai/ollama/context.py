"""Bounded structured context builder; full chat history is intentionally excluded."""

from __future__ import annotations

import json
from datetime import date
from typing import Any

from backend.app.engines.time_windows import records_in_window


def build_context(
    user: dict[str, Any],
    today_plan: dict[str, Any] | None,
    recent_sessions: list[dict[str, Any]],
    recovery_status: str,
    memories: dict[str, str],
    as_of: date | None = None,
) -> str:
    recent = records_in_window(recent_sessions, as_of or date.today(), 7)
    if recent_sessions and not any("workout_date" in item for item in recent_sessions):
        recent = list(recent_sessions)[max(0, len(recent_sessions) - 7) :]
    context = {
        "profile": {
            "age": user.get("age"),
            "training_experience": user.get("training_experience"),
            "available_days": user.get("available_training_days"),
            "session_duration_minutes": user.get("session_duration_minutes"),
            "equipment_mode": user.get("equipment_mode"),
            "noise_preference": user.get("noise_preference"),
            "jumping_allowed": bool(user.get("jumping_allowed", True)),
            "primary_goal": user.get("primary_goal"),
            "secondary_focus": user.get("secondary_focus"),
        },
        "today_plan": today_plan or {},
        "recent_workouts": [
            {
                "date": item.get("workout_date"),
                "status": item.get("status"),
                "rpe": item.get("session_rpe"),
                "soreness": item.get("soreness"),
                "pain": item.get("pain"),
                "fatigue": item.get("fatigue"),
            }
            for item in recent
        ],
        "recovery_status": recovery_status,
        "fitness_memory": memories,
    }
    return json.dumps(context, ensure_ascii=False, separators=(",", ":"))


class ContextBuilder:
    """Named boundary for the bounded context passed to a local model."""

    @staticmethod
    def build(
        user: dict[str, Any],
        today_plan: dict[str, Any] | None,
        recent_sessions: list[dict[str, Any]],
        recovery_status: str,
        memories: dict[str, str],
        as_of: date | None = None,
    ) -> str:
        return build_context(user, today_plan, recent_sessions, recovery_status, memories, as_of)
