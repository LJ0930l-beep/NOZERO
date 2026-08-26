"""Evidence-based progression decisions independent of AI."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

PROGRESSION_VARIABLES = ("reps", "sets", "tempo", "ROM", "leverage", "variation")
SUCCESS_STATUSES = {"FULL"}
FAILURE_STATUSES = {"ZERO", "RECOVERY"}


@dataclass(frozen=True)
class ProgressionDecision:
    decision: str
    reason: str
    next_step: str


def decide_progression(
    completion_rate: float,
    rpe: float | None,
    rir: float | None,
    form_quality: float,
    recovery_status: str,
    current_difficulty: int,
    tempo_quality: float = 1.0,
    rom_quality: float = 1.0,
    unilateral_quality: float = 1.0,
    sets_completed: int | None = None,
    leverage: str = "current",
) -> ProgressionDecision:
    if (
        recovery_status == "RECOVERY"
        or form_quality < 0.6
        or tempo_quality < 0.6
        or rom_quality < 0.6
        or unilateral_quality < 0.6
    ):
        return ProgressionDecision(
            "REGRESS",
            "recovery, form, tempo, range, or unilateral control is below the safe threshold",
            "reduce leverage, range, tempo, or volume",
        )
    if completion_rate < 0.75 or (rpe is not None and rpe >= 9.5) or (rir is not None and rir < 0.5):
        return ProgressionDecision(
            "REGRESS",
            "completion or effort indicates the current dose is too demanding",
            "reduce one variable before adding load",
        )
    if (
        completion_rate >= 0.9
        and form_quality >= 0.8
        and tempo_quality >= 0.8
        and rom_quality >= 0.8
        and unilateral_quality >= 0.8
        and (rpe is None or rpe <= 8.0)
        and (rir is None or rir >= 1.0)
    ):
        if current_difficulty >= 5:
            return ProgressionDecision(
                "PROGRESS", "quality completion at the top difficulty", "progress tempo, ROM, or density"
            )
        next_variable = "sets" if sets_completed is not None and sets_completed >= 2 else "reps"
        if tempo_quality < 0.95:
            next_variable = "tempo"
        elif rom_quality < 0.95:
            next_variable = "ROM"
        elif leverage != "current":
            next_variable = "leverage"
        elif unilateral_quality < 0.95:
            next_variable = "unilateral variation"
        return ProgressionDecision(
            "PROGRESS",
            "quality completion with reserve",
            f"move to the next safe progression or adjust {next_variable} by one small step",
        )
    return ProgressionDecision(
        "MAINTAIN",
        "evidence is mixed or insufficient for a change",
        "repeat the current variation and collect another session",
    )


def _matching_sessions(
    sessions: list[dict[str, Any]], exercise_id: str, limit: int = 3
) -> list[dict[str, Any]]:
    matching = []
    for session in sessions:
        plan = session.get("workout_plan")
        if not isinstance(plan, dict):
            continue
        blocks = plan.get("blocks") if isinstance(plan.get("blocks"), list) else []
        if any(isinstance(block, dict) and block.get("exercise_id") == exercise_id for block in blocks):
            matching.append(session)
    matching.sort(key=lambda item: (str(item.get("workout_date", "")), str(item.get("completed_at", ""))))
    return matching[-limit:]


def _block_for(session: dict[str, Any], exercise_id: str) -> dict[str, Any]:
    plan = session.get("workout_plan")
    if not isinstance(plan, dict):
        return {}
    blocks = plan.get("blocks") if isinstance(plan.get("blocks"), list) else []
    return next(
        (block for block in blocks if isinstance(block, dict) and block.get("exercise_id") == exercise_id),
        {},
    )


def _quality_flags(session: dict[str, Any], exercise_id: str) -> tuple[bool, bool]:
    status = str(session.get("status", ""))
    block = _block_for(session, exercise_id)
    completion = float(
        session.get("completion_rate", 1.0 if status == "FULL" else 0.5 if status == "MINIMUM" else 0.0)
    )
    rpe = session.get("session_rpe")
    rir = session.get("rir")
    pain = int(session.get("pain") or 0)
    form_quality = float(
        session.get("form_quality", 0.9 if status == "FULL" else 0.75 if status == "MINIMUM" else 0.5)
    )
    form_quality = min(form_quality, float(block.get("form_quality", form_quality)))
    success = (
        status in SUCCESS_STATUSES
        and completion >= 0.9
        and form_quality >= 0.8
        and pain <= 1
        and (rpe is None or float(rpe) <= 8)
        and (rir is None or float(rir) >= 1)
    )
    failure = (
        status in FAILURE_STATUSES
        or completion < 0.75
        or pain >= 4
        or form_quality < 0.6
        or (rpe is not None and float(rpe) >= 9.5)
        or (rir is not None and float(rir) < 0.5)
    )
    return success, failure


def _next_variable(current: str, target_reps: int | None, exercise: Mapping[str, Any]) -> str:
    variable = current if current in PROGRESSION_VARIABLES else "reps"
    if variable == "reps":
        maximum = int(exercise.get("rep_range", {}).get("max", 15))
        if target_reps is not None and target_reps >= maximum:
            return "sets"
    if variable == "sets" and int(exercise.get("recommended_sets", 3)) >= 4:
        return "tempo"
    if variable in {"tempo", "ROM", "leverage"}:
        return PROGRESSION_VARIABLES[PROGRESSION_VARIABLES.index(variable) + 1]
    return variable


def update_progression_state(
    user_id: str,
    exercise: dict[str, Any],
    sessions: list[dict[str, Any]],
    existing: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Aggregate the latest three performances into one durable state.

    A single abnormal performance is recorded but does not replace the current
    variation. Two consecutive weak performances are required before a
    regression is applied.
    """

    exercise_id = str(exercise["id"])
    recent = _matching_sessions(sessions, exercise_id, limit=3)
    if not recent:
        return existing or {
            "user_id": user_id,
            "exercise_id": exercise_id,
            "current_variation": exercise_id,
            "target_reps": exercise.get("rep_range", {}).get("min"),
            "target_sets": exercise.get("recommended_sets", 1),
            "last_rpe": None,
            "last_rir": None,
            "decision": "MAINTAIN",
            "next_variable": "reps",
            "consecutive_successes": 0,
            "consecutive_failures": 0,
        }

    success_flags = [_quality_flags(item, exercise_id)[0] for item in recent]
    failure_flags = [_quality_flags(item, exercise_id)[1] for item in recent]
    trailing_successes = 0
    for value in reversed(success_flags):
        if not value:
            break
        trailing_successes += 1
    trailing_failures = 0
    for value in reversed(failure_flags):
        if not value:
            break
        trailing_failures += 1

    latest = recent[-1]
    latest_block = _block_for(latest, exercise_id)
    current = dict(existing or {})
    current.update(
        {
            "user_id": user_id,
            "exercise_id": exercise_id,
            "current_variation": current.get("current_variation") or exercise_id,
            "target_reps": current.get("target_reps")
            or latest_block.get("reps")
            or exercise.get("rep_range", {}).get("min"),
            "target_sets": current.get("target_sets")
            or latest_block.get("sets")
            or exercise.get("recommended_sets", 1),
            "last_rpe": latest.get("session_rpe"),
            "last_rir": latest.get("rir"),
            "consecutive_successes": trailing_successes,
            "consecutive_failures": trailing_failures,
            "decision": "MAINTAIN",
            "next_variable": current.get("next_variable") or "reps",
        }
    )

    if trailing_successes >= 2:
        variable = str(current["next_variable"])
        current["decision"] = "PROGRESS"
        if variable == "reps":
            current["target_reps"] = min(
                int(exercise.get("rep_range", {}).get("max", current["target_reps"] or 15)),
                int(current["target_reps"] or 1) + 1,
            )
        elif variable == "sets":
            current["target_sets"] = min(5, int(current["target_sets"] or 1) + 1)
        elif variable == "variation":
            progression_ids = exercise.get("progression_ids", [])
            if progression_ids:
                current["current_variation"] = progression_ids[0]
                current["target_reps"] = None
        current["next_variable"] = _next_variable(variable, current.get("target_reps"), exercise)
    elif trailing_failures >= 2:
        current["decision"] = "REGRESS"
        regressions = exercise.get("regression_ids", [])
        if regressions:
            current["current_variation"] = regressions[0]
        else:
            current["target_reps"] = max(4, int(current.get("target_reps") or 6) - 2)
            current["target_sets"] = max(1, int(current.get("target_sets") or 1) - 1)
        current["next_variable"] = "reps"
    elif trailing_successes == 1 or trailing_failures == 1:
        current["decision"] = "MAINTAIN"

    return current


def apply_progression_to_block(
    block: dict[str, Any],
    state: dict[str, Any],
    exercises_by_id: Mapping[str, dict[str, Any]],
) -> dict[str, Any]:
    result = dict(block)
    current_variation = str(state.get("current_variation") or block.get("exercise_id"))
    if current_variation != str(block.get("exercise_id")) and current_variation in exercises_by_id:
        replacement = exercises_by_id[current_variation]
        result["exercise_id"] = current_variation
        result["name"] = replacement.get("name", result.get("name"))
        result["intent"] = (replacement.get("coaching_cues") or [result.get("intent", "controlled movement")])[0]
        if replacement.get("execution_type") == "duration":
            result["reps"] = None
            result["duration_seconds"] = int(replacement.get("duration_range", {}).get("min", 30))
        else:
            result["duration_seconds"] = None
            result["reps"] = int(replacement.get("rep_range", {}).get("min", result.get("reps") or 6))
    if state.get("decision") == "PROGRESS":
        if state.get("target_reps") is not None and result.get("reps") is not None:
            result["reps"] = int(state["target_reps"])
        if state.get("target_sets") is not None:
            result["sets"] = int(state["target_sets"])
        variable = str(state.get("next_variable", "reps"))
        if variable in {"tempo", "ROM", "leverage"}:
            labels = {"tempo": "节奏", "ROM": "活动范围", "leverage": "杠杆难度"}
            result["intent"] = f"{result.get('intent', 'controlled movement')} · {labels[variable]}推进一步"
    elif state.get("decision") == "REGRESS":
        result["sets"] = max(1, int(result.get("sets") or 1) - 1)
        if result.get("reps") is not None:
            result["reps"] = max(4, int(result["reps"]) - 2)
    return result


def apply_progression_states_to_plan(
    plan: list[dict[str, Any]],
    states: Mapping[str, dict[str, Any]],
    exercises_by_id: Mapping[str, dict[str, Any]],
    after_date: str,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for workout in plan:
        updated = dict(workout)
        if str(workout.get("date", "")) > after_date:
            updated["blocks"] = [
                apply_progression_to_block(block, states[str(block.get("exercise_id"))], exercises_by_id)
                if isinstance(block, dict) and str(block.get("exercise_id")) in states
                else block
                for block in workout.get("blocks", [])
            ]
        result.append(updated)
    return result
