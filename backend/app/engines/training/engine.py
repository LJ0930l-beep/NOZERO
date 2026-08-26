"""Scientific training planner: rules first, AI explanations second."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from backend.app.engines.progression.engine import apply_progression_states_to_plan
from backend.app.engines.training.load import weekly_cardio_target


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
        (0, 1, 3, 5),
        "Strength + conditioning",
        ("Squat", "Lunge", "Hip Hinge", "Core", "Cardio", "Horizontal Push"),
        3,
        True,
        "moderate",
        2,
    ),
    "abs": GoalProfile(
        (0, 2, 4, 6),
        "Core development + conditioning",
        ("Core Flexion", "Anti Extension", "Squat", "Cardio"),
        3,
        True,
        "moderate",
        2,
    ),
    "muscle_gain": GoalProfile(
        (0, 1, 3, 4),
        "Progressive resistance",
        ("Horizontal Push", "Pull", "Squat", "Hip Hinge", "Hip Extension", "Core"),
        4,
        False,
        "challenging",
        2,
    ),
    "body_shaping": GoalProfile(
        (0, 1, 3, 5),
        "Balanced resistance",
        ("Squat", "Lunge", "Hip Hinge", "Horizontal Push", "Core"),
        3,
        False,
        "moderate",
        2,
    ),
    "strength": GoalProfile(
        (0, 1, 3, 5),
        "Strength practice",
        ("Squat", "Hip Hinge", "Horizontal Push", "Pull", "Vertical Push", "Core"),
        4,
        False,
        "challenging",
        2,
    ),
    "cardio_fitness": GoalProfile(
        (0, 2, 4, 6), "Cardio + movement", ("Cardio", "Squat", "Core", "Mobility"), 2, True, "moderate", 2
    ),
    "core_strength": GoalProfile(
        (0, 1, 3, 5),
        "Core capacity",
        ("Anti Extension", "Core Flexion", "Lateral Core", "Squat"),
        3,
        False,
        "moderate",
        2,
    ),
    "mobility": GoalProfile(
        (0, 2, 4), "Mobility + control", ("Mobility", "Hip Extension", "Core", "Squat"), 2, False, "easy", 2
    ),
    "build_exercise_habit": GoalProfile(
        (0, 2, 4), "Low-friction habit", ("Squat", "Horizontal Push", "Core Flexion", "Mobility"), 2, False, "easy", 2
    ),
}


def _days_for_user(profile: GoalProfile, available_days: int) -> tuple[int, ...]:
    requested = max(1, min(7, available_days))
    if requested >= len(profile.schedule):
        return profile.schedule
    return profile.schedule[:requested]


PATTERN_DIMENSIONS = {
    "Horizontal Push": "upper_body",
    "Vertical Push": "upper_body",
    "Pull": "upper_body",
    "Squat": "lower_body",
    "Lunge": "lower_body",
    "Hip Hinge": "lower_body",
    "Hip Extension": "lower_body",
    "Core": "core",
    "Core Flexion": "core",
    "Anti Extension": "core",
    "Anti Rotation": "core",
    "Lateral Core": "core",
    "Cardio": "cardio",
    "Mobility": "mobility",
}

SECONDARY_PATTERNS = {
    "abs": ("Core Flexion", "Anti Extension", "Lateral Core", "Core"),
    "chest": ("Horizontal Push",),
    "back": ("Pull", "Hip Hinge"),
    "shoulders": ("Vertical Push", "Horizontal Push"),
    "arms": ("Horizontal Push", "Pull"),
    "glutes": ("Hip Extension", "Lunge", "Squat"),
    "legs": ("Squat", "Lunge", "Hip Hinge"),
    "mobility": ("Mobility",),
}

PHASES = ("Adaptation / Base", "Progress", "Progress", "Consolidation / Reassessment")
LOWER_BODY_PATTERNS = {"Squat", "Lunge", "Hip Hinge", "Hip Extension"}
RESTRICTION_ALTERNATIVES = {
    "Horizontal Push": ("Anti Extension", "Core", "Mobility"),
    "Vertical Push": ("Anti Extension", "Core", "Mobility"),
    "Lunge": ("Squat", "Hip Extension", "Core"),
}
PATTERN_LABELS_ZH = {
    "Horizontal Push": "水平推",
    "Vertical Push": "垂直推",
    "Pull": "拉",
    "Squat": "深蹲",
    "Lunge": "弓步",
    "Hip Hinge": "髋铰链",
    "Hip Extension": "髋伸展",
    "Core": "核心",
    "Core Flexion": "核心屈曲",
    "Anti Extension": "抗伸展",
    "Anti Rotation": "抗旋转",
    "Lateral Core": "侧向核心",
    "Cardio": "心肺",
    "Mobility": "灵活性",
}
GOAL_TITLES_ZH = {
    "Strength + conditioning": "力量 + 体能",
    "Core development + conditioning": "核心发展 + 体能",
    "Progressive resistance": "渐进抗阻",
    "Balanced resistance": "平衡抗阻",
    "Strength practice": "力量练习",
    "Cardio + movement": "心肺 + 活动",
    "Core capacity": "核心能力",
    "Mobility + control": "灵活性 + 控制",
    "Low-friction habit": "低门槛习惯",
}


def _focus_order(goal_profile: GoalProfile, secondary_focus: str | None) -> tuple[str, ...]:
    preferred = SECONDARY_PATTERNS.get(str(secondary_focus or "").lower(), ())
    if not preferred:
        return goal_profile.focus_order
    ordered = list(goal_profile.focus_order)
    for pattern in reversed(preferred):
        if pattern in ordered:
            ordered.remove(pattern)
        ordered.insert(0, pattern)
    return tuple(ordered)


def _difficulty_cap(assessment: dict[str, str] | None, pattern: str) -> int | None:
    if not assessment:
        return None
    dimension = PATTERN_DIMENSIONS.get(pattern)
    levels = [assessment.get(dimension)] if dimension else list(assessment.values())
    numeric = [int(level[1]) for level in levels if isinstance(level, str) and len(level) == 2 and level[0] == "F"]
    return max(1, min(5, round(sum(numeric) / len(numeric)))) if numeric else None


def _assessment_average(assessment: dict[str, str] | None) -> float:
    if not assessment:
        return 3.0
    numeric = [
        int(level[1])
        for level in assessment.values()
        if isinstance(level, str) and len(level) == 2 and level[0] == "F"
    ]
    return sum(numeric) / len(numeric) if numeric else 3.0


def _history_signal(recent_sessions: list[dict[str, Any]] | None) -> str:
    if not recent_sessions:
        return "MAINTAIN"
    recent = recent_sessions[-3:]
    severe = [
        item
        for item in recent
        if item.get("status") == "RECOVERY"
        or int(item.get("pain") or 0) >= 4
        or int(item.get("fatigue") or 0) >= 8
    ]
    if len(severe) >= 2:
        return "REGRESS"
    quality = [
        item
        for item in recent
        if item.get("status") == "FULL"
        and float(item.get("session_rpe") or 10) <= 8
        and float(item.get("rir") or 0) >= 1
        and int(item.get("pain") or 0) <= 1
    ]
    if len(quality) >= 2 and all(item in quality for item in recent[-2:]):
        return "PROGRESS"
    return "MAINTAIN"


def _pick_exercise(
    exercises: list[dict[str, Any]], pattern: str, used: set[str], difficulty_cap: int | None = None
) -> dict[str, Any] | None:
    candidates = [item for item in exercises if item["movement_pattern"] == pattern and item["id"] not in used]
    if not candidates:
        return None
    ordered = sorted(
        candidates,
        key=lambda item: (
            0 if item.get("selection_status", "SAFE") == "SAFE" else 1,
            int(item.get("difficulty_level", 1)),
            item["id"],
        ),
    )
    if difficulty_cap is None:
        return ordered[0]
    eligible = [item for item in ordered if int(item.get("difficulty_level", 1)) <= difficulty_cap]
    return eligible[-1] if eligible else ordered[0]


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
            "name": exercise.get("name_cn") or exercise["name"],
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
        "name": exercise.get("name_cn") or exercise["name"],
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


def build_short_workout(workout: dict[str, Any], block_count: int = 3) -> list[dict[str, Any]]:
    """Create a plan-derived rescue dose between the full and minimum versions."""
    if workout.get("kind") == "RECOVERY":
        return list(workout.get("blocks", []))[:1]
    blocks = list(workout.get("blocks", []))[: max(1, block_count)]
    short: list[dict[str, Any]] = []
    for block in blocks:
        reduced = dict(block)
        reduced["sets"] = max(1, (int(reduced.get("sets", 1)) + 1) // 2)
        if reduced.get("reps") is not None:
            reduced["reps"] = min(int(reduced["reps"]), 12)
        if reduced.get("duration_seconds") is not None:
            reduced["duration_seconds"] = min(int(reduced["duration_seconds"]), 60)
        reduced["rest_seconds"] = max(30, int(reduced.get("rest_seconds", 60)) // 2)
        reduced["minimum"] = False
        short.append(reduced)
    return short


def generate_cycle(
    profile: dict[str, Any],
    exercises: list[dict[str, Any]],
    assessment: dict[str, str] | None,
    start_date: date,
    cycle_days: int,
    recent_sessions: list[dict[str, Any]] | None = None,
    recovery_status: str = "NORMAL",
    recent_load: dict[str, Any] | None = None,
    progression_states: Mapping[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    goal = str(profile.get("primary_goal", "build_exercise_habit"))
    goal_profile = GOAL_PROFILES.get(goal, GOAL_PROFILES["build_exercise_habit"])
    focus_order = _focus_order(goal_profile, profile.get("secondary_focus"))
    training_days = set(_days_for_user(goal_profile, int(profile.get("available_training_days", 3))))
    session_minutes = int(profile.get("session_duration_minutes", 20))
    noise_preference = profile.get("noise_preference", "NORMAL")
    jumping_allowed = bool(profile.get("jumping_allowed", True))
    history_signal = _history_signal(recent_sessions)
    recovery_reduction = recovery_status in {"REDUCED", "RECOVERY", "SWAP_FOCUS"}
    recent_pattern_sets = dict((recent_load or {}).get("recent_pattern_sets", {}))
    lower_body_load = sum(float(recent_pattern_sets.get(pattern, 0)) for pattern in LOWER_BODY_PATTERNS)
    selected_days: list[dict[str, Any]] = []
    for index in range(cycle_days):
        current_date = start_date + timedelta(days=index)
        week_number = index // 7 + 1
        phase = PHASES[min(week_number - 1, len(PHASES) - 1)]
        cardio_target_minutes = weekly_cardio_target(profile, assessment, week_number - 1)
        weekday = index % 7
        if weekday not in training_days:
            recovery = {
                "date": current_date.isoformat(),
                "day_index": index,
                "title": "计划恢复",
                "focus": "恢复 / 灵活性",
                "duration_minutes": min(session_minutes, 10),
                "kind": "RECOVERY",
                "blocks": [],
                "week_number": week_number,
                "phase": phase,
                "cardio_target_minutes": cardio_target_minutes,
            }
            recovery["minimum_workout"] = []
            recovery["short_workout"] = []
            selected_days.append(recovery)
            continue
        used: set[str] = set()
        blocks: list[dict[str, Any]] = []
        for pattern in focus_order:
            if lower_body_load >= 6 and pattern in LOWER_BODY_PATTERNS:
                continue
            difficulty_cap = _difficulty_cap(assessment, pattern)
            if difficulty_cap is not None and history_signal == "REGRESS":
                difficulty_cap = max(1, difficulty_cap - 1)
            elif difficulty_cap is not None and history_signal == "PROGRESS":
                difficulty_cap = min(5, difficulty_cap + 1)
            candidate = _pick_exercise(exercises, pattern, used, difficulty_cap)
            if candidate is None:
                for alternative_pattern in RESTRICTION_ALTERNATIVES.get(pattern, ()):
                    alternative = _pick_exercise(exercises, alternative_pattern, used, difficulty_cap)
                    if alternative is not None and alternative["id"] not in used:
                        candidate = alternative
                        break
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
            if _assessment_average(assessment) >= 4 and profile.get("training_experience") != "new":
                sets = min(4, sets + 1)
            if history_signal == "REGRESS" or recovery_reduction:
                sets = max(1, sets - 1)
            if candidate.get("selection_status") == "CAUTION":
                sets = max(1, sets - 1)
            intensity = "easy" if recovery_reduction else goal_profile.intensity
            block = _block(candidate, sets, intensity)
            if candidate.get("selection_status") == "CAUTION":
                block["intent"] = f"{block['intent']} · conservative range"
            blocks.append(block)
        if not blocks:
            recovery = {
                "date": current_date.isoformat(),
                "day_index": index,
                "title": "计划恢复",
                "focus": "恢复 / 灵活性",
                "duration_minutes": min(session_minutes, 10),
                "kind": "RECOVERY",
                "blocks": [],
                "minimum_workout": [],
                "short_workout": [],
                "week_number": week_number,
                "phase": phase,
                "cardio_target_minutes": cardio_target_minutes,
            }
            selected_days.append(recovery)
            continue
        if goal_profile.cardio_blocks and not any(block["exercise_id"].startswith("cardio") for block in blocks):
            cardio = _pick_exercise(exercises, "Cardio", used)
            if cardio and (jumping_allowed or cardio["impact_level"] != "HIGH"):
                blocks.append(_block(cardio, 1, goal_profile.intensity))
        if not recovery_reduction and week_number == 2:
            for block in blocks:
                block["sets"] = min(5, int(block.get("sets", 1)) + 1)
        elif not recovery_reduction and week_number == 3:
            for block in blocks:
                if block.get("reps") is not None:
                    block["reps"] = int(block["reps"]) + 2
                elif block.get("duration_seconds") is not None:
                    block["duration_seconds"] = int(block["duration_seconds"]) + 15
        elif week_number >= 4:
            for block in blocks:
                block["sets"] = max(1, int(block.get("sets", 1)) - 1)
        workout = {
            "date": current_date.isoformat(),
            "day_index": index,
            "title": GOAL_TITLES_ZH.get(goal_profile.title, goal_profile.title),
            "focus": " + ".join(PATTERN_LABELS_ZH.get(pattern, pattern) for pattern in focus_order[:2]),
            "duration_minutes": min(session_minutes, max(6, len(blocks) * 4 + 4)),
            "kind": "TRAINING",
            "blocks": blocks,
            "week_number": week_number,
            "phase": phase,
            "cardio_target_minutes": cardio_target_minutes,
        }
        workout["short_workout"] = build_short_workout(workout, max(goal_profile.minimum_blocks + 1, 3))
        workout["minimum_workout"] = build_minimum_workout(workout, goal_profile.minimum_blocks)
        selected_days.append(workout)
    if progression_states:
        exercise_lookup = {str(item["id"]): item for item in exercises}
        selected_days = apply_progression_states_to_plan(
            selected_days,
            progression_states,
            exercise_lookup,
            (start_date - timedelta(days=1)).isoformat(),
        )
        for workout in selected_days:
            if workout.get("kind") == "TRAINING":
                workout["short_workout"] = build_short_workout(workout, max(goal_profile.minimum_blocks + 1, 3))
                workout["minimum_workout"] = build_minimum_workout(workout, goal_profile.minimum_blocks)
    return selected_days
