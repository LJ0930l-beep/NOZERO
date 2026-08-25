"""Deterministic weekly review metrics for optional local-model narration."""

from __future__ import annotations

from typing import Any


class WeeklyReview:
    """Builds review numbers only from stored structured workout sessions."""

    @staticmethod
    def summarize(sessions: list[dict[str, Any]]) -> dict[str, Any]:
        recent = sessions[-7:]
        successful = [item for item in recent if item.get("status") in {"FULL", "MINIMUM", "RECOVERY"}]
        total_minutes = sum(
            int(item.get("workout_plan", {}).get("duration_minutes", 0))
            for item in recent
            if isinstance(item.get("workout_plan"), dict)
        )
        return {
            "sessions_completed": len(successful),
            "consistency": round(len(successful) / 7 * 100, 1),
            "training_time_minutes": total_minutes,
            "full_days": sum(item.get("status") == "FULL" for item in recent),
            "minimum_days": sum(item.get("status") == "MINIMUM" for item in recent),
            "recovery_days": sum(item.get("status") == "RECOVERY" for item in recent),
            "zero_days": sum(item.get("status") == "ZERO" for item in recent),
        }
