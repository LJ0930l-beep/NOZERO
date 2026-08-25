"""Scientific training planner: rules first, AI explanations second."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any


@dataclass(frozen=True)
class GoalProfile:
    schedule: tuple[int, ...]
    title: str
    focus_order: tuple[str, ...]
    base_sets: int
    cardio_blocks: bool
    intensity: str
    minimum_blocks: int


GOAL_PROFILES: dict[str, GoalProfile] = {
    "fat_loss": GoalProfile(
        (0, 1, 3, 5), "Strength + conditioning", ("Squat", "Core", "Cardio", "Horizontal Push"), 3, True, "moderate", 2
    ),
    "abs": GoalProfile(
        (0, 2, 4, 6),
        "Core development + conditioning",
        ("Core", "Anti Extension", "Squat", "Cardio"),
        3,
        True,
        "moderate",
        2,
    ),
    "muscle_gain": GoalProfile(
        (0, 1, 3, 4),
        "Progressive resistance",
        ("Horizontal Push", "Squat", "Hip Extension", "Core"),
        4,
        False,
        "challenging",
        2,
    ),
    "body_shaping": GoalProfile(
        (0, 1, 3, 5),
        "Balanced resistance",
        ("Squat", "Horizontal Push", "Hip Extension", "Core"),
        3,
        False,
        "moderate",
        2,
    ),
    "strength": GoalProfile(
        (0, 1, 3, 5),
        "Strength practice",
        ("Squat", "Horizontal Push", "Vertical Push", "Core"),
        4,
        False,
        "challenging",
        2,
    ),
    "cardio_fitness": GoalProfile(
        (0, 2, 4, 6), "Cardio + movement", ("Cardio", "Squat", "Core", "Mobility"), 2, True, "moderate", 2
    ),
    "core_strength": GoalProfile(
        (0, 1, 3, 5), "Core capacity", ("Anti Extension", "Lateral Core", "Core", "Squat"), 3, False, "moderate", 2
    ),
    "mobility": GoalProfile(
        (0, 2, 4), "Mobility + control", ("Mobility", "Hip Extension", "Core", "Squat"), 2, False, "easy", 2
    ),
    "build_exercise_habit": GoalProfile(
        (0, 2, 4), "Low-friction habit", ("Squat", "Horizontal Push", "Core", "Mobility"), 2, False, "easy", 2
    ),
}


def _days_for_user(profile: GoalProfile, available_days: int) -> tuple[int, ...]:
    requested = max(1, min(7, available_days))
    if requested >= len(profile.schedule):
        return profile.schedule
    return profile.schedule[:requested]


def _pick_exercise(exercises: list[dict[str, Any]], pattern: str, used: set[str]) -> dict[str, Any] | None:
    candidates = [item for item in exercises if item["movement_pattern"] == pattern and item["id"] not in used]
    if not candidates:
        candidates = [item for item in exercises if item["movement_pattern"] == pattern]
    return candidates[0] if candidates else None


def _block(exercise: dict[str, Any], sets: int, intensity: str, minimum: bool = False) -> dict[str, Any]:
    rep_range = exercise.get("rep_range", {})
    duration_range = exercise.get("duration_range", {})
    if exercise.get("execution_type") == "duration":
        duration = int(duration_range.get("min", 20))
        if intensity == "challenging":
            duration = int(duration_range.get("max", duration))
        if minimum:
            duration = min(duration, 30)
        return {
            "exercise_id": exercise["id"],
            "name": exercise["name"],
            "sets": 1 if minimum else sets,
            "reps": None,
            "duration_seconds": duration,
            "rest_seconds": 30 if minimum else 60,
            "intent": exercise.get("coaching_cues", ["controlled movement"])[0],
            "minimum": minimum,
        }
    reps = int(rep_range.get("min", 6))
    if intensity == "easy":
        reps = max(4, reps)
    elif intensity == "challenging":
        reps = int(rep_range.get("max", reps))
    if minimum:
        reps = min(reps, 8)
    return {
        "exercise_id": exercise["id"],
        "name": exercise["name"],
        "sets": 1 if minimum else sets,
        "reps": reps,
        "duration_seconds": None,
        "rest_seconds": 30 if minimum else 75,
        "intent": exercise.get("coaching_cues", ["controlled movement"])[0],
        "minimum": minimum,
    }


def build_minimum_workout(workout: dict[str, Any], block_count: int = 2) -> list[dict[str, Any]]:
    if workout.get("kind") == "RECOVERY":
        return list(workout.get("blocks", []))[:1]
    blocks = list(workout.get("blocks", []))[: max(1, block_count)]
    minimum: list[dict[str, Any]] = []
    for block in blocks:
        reduced = dict(block)
        reduced["sets"] = 1
        reduced["minimum"] = True
        if reduced.get("reps") is not None:
            reduced["reps"] = min(int(reduced["reps"]), 8)
        if reduced.get("duration_seconds") is not None:
            reduced["duration_seconds"] = min(int(reduced["duration_seconds"]), 30)
        reduced["rest_seconds"] = 20
        minimum.append(reduced)
    return minimum


def generate_cycle(
    profile: dict[str, Any],
    exercises: list[dict[str, Any]],
    assessment: dict[str, str] | None,
    start_date: date,
    cycle_days: int,
) -> list[dict[str, Any]]:
    goal = str(profile.get("primary_goal", "build_exercise_habit"))
    goal_profile = GOAL_PROFILES.get(goal, GOAL_PROFILES["build_exercise_habit"])
    training_days = set(_days_for_user(goal_profile, int(profile.get("available_training_days", 3))))
    session_minutes = int(profile.get("session_duration_minutes", 20))
    noise_preference = profile.get("noise_preference", "NORMAL")
    jumping_allowed = bool(profile.get("jumping_allowed", True))
    selected_days: list[dict[str, Any]] = []
    for index in range(cycle_days):
        current_date = start_date + timedelta(days=index)
        weekday = index % 7
        if weekday not in training_days:
            recovery = {
                "date": current_date.isoformat(),
                "day_index": index,
                "title": "Planned recovery",
                "focus": "Recovery / mobility",
                "duration_minutes": min(session_minutes, 10),
                "kind": "RECOVERY",
                "blocks": [],
            }
            recovery["minimum_workout"] = []
            selected_days.append(recovery)
            continue
        used: set[str] = set()
        blocks: list[dict[str, Any]] = []
        for pattern in goal_profile.focus_order:
            candidate = _pick_exercise(exercises, pattern, used)
            if candidate is None:
                continue
            if noise_preference == "QUIET" and candidate["noise_level"] == "HIGH":
                continue
            if not jumping_allowed and candidate["impact_level"] == "HIGH":
                continue
            used.add(candidate["id"])
            sets = goal_profile.base_sets
            if profile.get("training_experience") == "new":
                sets = max(1, sets - 1)
            blocks.append(_block(candidate, sets, goal_profile.intensity))
        if not blocks:
            recovery = {
                "date": current_date.isoformat(),
                "day_index": index,
                "title": "Planned recovery",
                "focus": "Recovery / mobility",
                "duration_minutes": min(session_minutes, 10),
                "kind": "RECOVERY",
                "blocks": [],
                "minimum_workout": [],
            }
            selected_days.append(recovery)
            continue
        if goal_profile.cardio_blocks and not any(block["exercise_id"].startswith("cardio") for block in blocks):
            cardio = _pick_exercise(exercises, "Cardio", used)
            if cardio and (jumping_allowed or cardio["impact_level"] != "HIGH"):
                blocks.append(_block(cardio, 1, goal_profile.intensity))
        workout = {
            "date": current_date.isoformat(),
            "day_index": index,
            "title": goal_profile.title,
            "focus": " + ".join(goal_profile.focus_order[:2]),
            "duration_minutes": min(session_minutes, max(6, len(blocks) * 4 + 4)),
            "kind": "TRAINING",
            "blocks": blocks,
        }
        workout["minimum_workout"] = build_minimum_workout(workout, goal_profile.minimum_blocks)
        selected_days.append(workout)
    return selected_days
