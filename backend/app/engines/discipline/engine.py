"""Discipline metrics where planned recovery counts as execution."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date, timedelta

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
