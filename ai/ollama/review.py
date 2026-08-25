"""Deterministic weekly review metrics for optional local-model narration."""

from __future__ import annotations

from typing import Any


class WeeklyReview:
    """Builds review numbers only from stored structured workout sessions."""

    @staticmethod
    def compare_assessments(assessments: list[dict[str, Any]]) -> dict[str, dict[str, str | int]]:
        if len(assessments) < 2:
            return {}
        before = assessments[0].get("dimensions", {})
        after = assessments[-1].get("dimensions", {})
        comparison: dict[str, dict[str, str | int]] = {}
        for dimension, current in after.items():
            previous = before.get(dimension, current)
            if (
                isinstance(previous, str)
                and isinstance(current, str)
                and len(previous) == 2
                and len(current) == 2
                and previous[0] == "F"
                and current[0] == "F"
            ):
                comparison[dimension] = {
                    "before": previous,
                    "after": current,
                    "delta": int(current[1]) - int(previous[1]),
                }
        return comparison

    @staticmethod
    def summarize(
        sessions: list[dict[str, Any]], assessments: list[dict[str, Any]] | None = None
    ) -> dict[str, Any]:
        recent = sessions[-7:]
        successful = [item for item in recent if item.get("status") in {"FULL", "MINIMUM", "RECOVERY"}]
        total_minutes = sum(
            int(item.get("workout_plan", {}).get("duration_minutes", 0))
            for item in recent
            if item.get("status") in {"FULL", "MINIMUM", "RECOVERY"}
            and isinstance(item.get("workout_plan"), dict)
        )
        comparison = WeeklyReview.compare_assessments(assessments or [])
        return {
            "sessions_completed": len(successful),
            "consistency": round(len(successful) / 7 * 100, 1),
            "training_time_minutes": total_minutes,
            "full_days": sum(item.get("status") == "FULL" for item in recent),
            "minimum_days": sum(item.get("status") == "MINIMUM" for item in recent),
            "recovery_days": sum(item.get("status") == "RECOVERY" for item in recent),
            "zero_days": sum(item.get("status") == "ZERO" for item in recent),
            "performance_change": comparison,
            "fitness_progress": {
                "improved_dimensions": [key for key, value in comparison.items() if int(value["delta"]) > 0],
                "average_delta": round(
                    sum(int(value["delta"]) for value in comparison.values()) / len(comparison), 1
                )
                if comparison
                else 0,
            },
        }
