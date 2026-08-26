"""Discipline metrics where planned recovery counts as execution."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date, timedelta
from typing import Any

from backend.app.engines.time_windows import due_plan_dates, parse_local_date

SUCCESS_STATES = {"FULL", "MINIMUM", "RECOVERY"}
XP_BY_STATUS = {"FULL": 100, "MINIMUM": 30, "RECOVERY": 20, "ZERO": 0}


def xp_for_status(status: str) -> int:
    return XP_BY_STATUS.get(status, 0)


def _success_dates(sessions: Iterable[dict[str, object]]) -> set[date]:
    dates: set[date] = set()
    for session in sessions:
        if str(session.get("status")) not in SUCCESS_STATES:
            continue
        raw_date = str(session.get("workout_date", ""))
        try:
            dates.add(date.fromisoformat(raw_date))
        except ValueError:
            continue
    return dates


def streaks(sessions: list[dict[str, object]], as_of: date | None = None) -> tuple[int, int]:
    success_dates = _success_dates(sessions)
    if not success_dates:
        return 0, 0
    cursor = as_of or max(success_dates)
    current = 0
    while cursor in success_dates:
        current += 1
        cursor -= timedelta(days=1)
    longest = 0
    run = 0
    previous: date | None = None
    for day in sorted(success_dates):
        if previous and day == previous + timedelta(days=1):
            run += 1
        else:
            run = 1
        longest = max(longest, run)
        previous = day
    return current, longest


def consistency(sessions: list[dict[str, object]], as_of: date | None = None) -> dict[str, dict[str, int | float]]:
    reference = as_of or date.today()
    dates = _success_dates(sessions)
    result: dict[str, dict[str, int | float]] = {}
    for window in (7, 28, 90):
        start = reference - timedelta(days=window - 1)
        completed = sum(1 for day in dates if start <= day <= reference)
        result[str(window)] = {
            "completed": completed,
            "planned": window,
            "percentage": round(completed / window * 100, 1),
        }
    return result


def _plan_success(workout: dict[str, Any], status: str | None) -> bool:
    if status in SUCCESS_STATES:
        return True
    return status in {None, "DUE"} and workout.get("kind") == "RECOVERY"


def plan_adherence(
    plan: list[dict[str, Any]],
    executions: list[dict[str, Any]],
    as_of: date | None = None,
) -> dict[str, int | float]:
    """Measure execution against due plan days, including unlogged recovery days."""

    reference = as_of or date.today()
    due = due_plan_dates(plan, reference)
    status_by_date = {str(item.get("plan_date")): str(item.get("status")) for item in executions}
    completed = sum(
        _plan_success(workout, status_by_date.get(str(workout.get("date")))) for workout in due
    )
    recovery_days = sum(
        _plan_success(workout, status_by_date.get(str(workout.get("date"))))
        and workout.get("kind") == "RECOVERY"
        for workout in due
    )
    zero_days = sum(status_by_date.get(str(workout.get("date"))) == "ZERO" for workout in due)
    planned = len(due)
    return {
        "completed": int(completed),
        "planned": planned,
        "percentage": round(completed / planned * 100, 1) if planned else 0.0,
        "recovery_days": int(recovery_days),
        "zero_days": int(zero_days),
    }


def plan_streak(
    plan: list[dict[str, Any]],
    executions: list[dict[str, Any]],
    as_of: date | None = None,
) -> tuple[int, int]:
    """Return current/longest streak over consecutive due plan days."""

    reference = as_of or date.today()
    due = due_plan_dates(plan, reference)
    if not due:
        return 0, 0
    status_by_date = {str(item.get("plan_date")): str(item.get("status")) for item in executions}
    success_dates = {
        parse_local_date(workout.get("date"))
        for workout in due
        if _plan_success(workout, status_by_date.get(str(workout.get("date"))))
    }
    success_dates.discard(None)
    cursor = parse_local_date(due[-1].get("date"))
    current = 0
    while cursor is not None and cursor in success_dates:
        current += 1
        cursor -= timedelta(days=1)
    longest = 0
    run = 0
    for workout in due:
        workout_date = parse_local_date(workout.get("date"))
        if workout_date in success_dates:
            run += 1
            longest = max(longest, run)
        else:
            run = 0
    return current, longest


def discipline_level(total_xp: int) -> str:
    if total_xp >= 5000:
        return "D5 Unbreakable"
    if total_xp >= 2500:
        return "D4 Disciplined"
    if total_xp >= 1000:
        return "D3 Focused"
    if total_xp >= 300:
        return "D2 Consistent"
    return "D1 Starter"


def achievements(sessions: list[dict[str, object]], total_xp: int) -> list[str]:
    """Small, local milestones; achievements never change training or safety rules."""
    success = [item for item in sessions if str(item.get("status")) in SUCCESS_STATES]
    _, longest = streaks(sessions)
    earned: list[str] = []
    if success:
        earned.append("first_session")
    if any(str(item.get("status")) == "MINIMUM" for item in sessions):
        earned.append("rescue_kept")
    if any(str(item.get("status")) == "RECOVERY" for item in sessions):
        earned.append("recovery_is_training")
    if longest >= 7:
        earned.append("seven_day_streak")
    if total_xp >= 1000:
        earned.append("one_thousand_xp")
    return earned
