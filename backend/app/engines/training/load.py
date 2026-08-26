"""Training load accounting by movement pattern and muscle exposure."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from backend.app.engines.time_windows import records_in_window

PRIMARY_SET_WEIGHT = 1.0
SECONDARY_SET_WEIGHT = 0.5


@dataclass
class TrainingLoad:
    muscle_sets: dict[str, float] = field(default_factory=dict)
    pattern_sets: dict[str, float] = field(default_factory=dict)
    cardio_minutes: float = 0.0
    daily_movement_minutes: float = 0.0
    total_training_minutes: float = 0.0
    sessions_count: int = 0
    recent_pattern_sets: dict[str, float] = field(default_factory=dict)

    @property
    def max_muscle_sets(self) -> float:
        return max(self.muscle_sets.values(), default=0.0)

    def as_dict(self) -> dict[str, Any]:
        return {
            "muscle_sets": dict(self.muscle_sets),
            "pattern_sets": dict(self.pattern_sets),
            "cardio_minutes": round(self.cardio_minutes, 1),
            "daily_movement_minutes": round(self.daily_movement_minutes, 1),
            "total_training_minutes": round(self.total_training_minutes, 1),
            "sessions_count": self.sessions_count,
            "recent_pattern_sets": dict(self.recent_pattern_sets),
        }


def _exercise_lookup(exercises: Mapping[str, dict[str, Any]] | list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    if isinstance(exercises, Mapping):
        return dict(exercises)
    return {str(item.get("id")): item for item in exercises}


def _add(mapping: dict[str, float], key: str, value: float) -> None:
    if key:
        mapping[key] = round(mapping.get(key, 0.0) + value, 2)


def _session_load(
    session: dict[str, Any], lookup: Mapping[str, dict[str, Any]]
) -> tuple[dict[str, float], dict[str, float], float, float]:
    muscle_sets: dict[str, float] = {}
    pattern_sets: dict[str, float] = {}
    cardio_minutes = 0.0
    plan = session.get("workout_plan")
    if not isinstance(plan, dict):
        return muscle_sets, pattern_sets, cardio_minutes, 0.0
    blocks = plan.get("blocks") if isinstance(plan.get("blocks"), list) else []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        exercise = lookup.get(str(block.get("exercise_id")), {})
        sets = max(1, int(block.get("sets") or 1))
        pattern = str(exercise.get("movement_pattern") or block.get("movement_pattern") or "")
        _add(pattern_sets, pattern, float(sets))
        for muscle in exercise.get("primary_muscles", []):
            _add(muscle_sets, str(muscle), sets * PRIMARY_SET_WEIGHT)
        for muscle in exercise.get("secondary_muscles", []):
            _add(muscle_sets, str(muscle), sets * SECONDARY_SET_WEIGHT)
        if pattern == "Cardio" or str(block.get("exercise_id", "")).startswith("cardio"):
            cardio_minutes += sets * float(block.get("duration_seconds") or 0) / 60
    plan_minutes = float(plan.get("duration_minutes") or 0)
    if plan_minutes <= 0:
        plan_minutes = sum(
            max(0.0, float(block.get("sets") or 1) * float(block.get("duration_seconds") or 0) / 60)
            for block in blocks
            if isinstance(block, dict)
        )
    return muscle_sets, pattern_sets, cardio_minutes, plan_minutes


def calculate_training_load(
    sessions: list[dict[str, Any]],
    exercises: Mapping[str, dict[str, Any]] | list[dict[str, Any]],
    reference_date: date,
    window_days: int = 7,
    wellness_logs: list[dict[str, Any]] | None = None,
) -> TrainingLoad:
    """Calculate only successful sessions inside an inclusive date window."""

    lookup = _exercise_lookup(exercises)
    window_sessions = records_in_window(sessions, reference_date, window_days)
    successful = [
        item for item in window_sessions if str(item.get("status")) in {"FULL", "MINIMUM", "RECOVERY"}
    ]
    load = TrainingLoad(sessions_count=len(successful))
    for session in successful:
        muscles, patterns, cardio, minutes = _session_load(session, lookup)
        for key, value in muscles.items():
            _add(load.muscle_sets, key, value)
        for key, value in patterns.items():
            _add(load.pattern_sets, key, value)
        load.cardio_minutes += cardio
        load.total_training_minutes += minutes

    recent_sessions = records_in_window(successful, reference_date, min(window_days, 2))
    for session in recent_sessions:
        _, patterns, _, _ = _session_load(session, lookup)
        for key, value in patterns.items():
            _add(load.recent_pattern_sets, key, value)

    if wellness_logs:
        for log in records_in_window(wellness_logs, reference_date, window_days, field="log_date"):
            load.daily_movement_minutes += float(log.get("daily_movement_minutes") or 0)
    load.cardio_minutes = round(load.cardio_minutes, 1)
    load.daily_movement_minutes = round(load.daily_movement_minutes, 1)
    load.total_training_minutes = round(load.total_training_minutes, 1)
    return load


CARDIO_TARGET_MINUTES = {
    "cardio_fitness": 120,
    "fat_loss": 90,
    "abs": 75,
    "body_shaping": 60,
    "muscle_gain": 45,
    "strength": 45,
    "core_strength": 45,
    "build_exercise_habit": 30,
    "mobility": 30,
}


def weekly_cardio_target(
    profile: dict[str, Any],
    assessment: dict[str, str] | None = None,
    week_index: int = 0,
) -> int:
    """Return a conservative, goal-aware weekly aerobic dose."""

    goal = str(profile.get("primary_goal", "build_exercise_habit"))
    target = CARDIO_TARGET_MINUTES.get(goal, 45)
    level = (assessment or {}).get("cardio", "F1")
    if isinstance(level, str) and len(level) == 2 and level[0] == "F":
        target += max(0, int(level[1]) - 1) * 5
    target += min(max(0, week_index), 3) * 5
    return int(target)


def aerobic_dose(load: TrainingLoad, target_minutes: int) -> dict[str, int | float]:
    completed = round(load.cardio_minutes + load.daily_movement_minutes, 1)
    percentage = round(min(100.0, completed / target_minutes * 100) if target_minutes else 0.0, 1)
    return {
        "target_minutes": target_minutes,
        "completed_minutes": completed,
        "percentage": percentage,
    }
