"""Shared local-date windows for recovery, reviews, and adherence metrics."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any


@dataclass(frozen=True)
class DateWindow:
    """Inclusive local calendar-date window."""

    start: date
    end: date

    def contains(self, value: date) -> bool:
        return self.start <= value <= self.end


def date_window(reference: date, days: int) -> DateWindow:
    """Return exactly ``days`` local dates ending on ``reference``."""

    if days < 1:
        raise ValueError("a date window must contain at least one day")
    return DateWindow(reference - timedelta(days=days - 1), reference)


def parse_local_date(value: Any) -> date | None:
    raw = str(value or "")[:10]
    try:
        return date.fromisoformat(raw)
    except (TypeError, ValueError):
        return None


def records_in_window(
    records: Iterable[dict[str, Any]],
    reference: date,
    days: int,
    field: str = "workout_date",
) -> list[dict[str, Any]]:
    window = date_window(reference, days)
    return [
        record
        for record in records
        if (record_date := parse_local_date(record.get(field))) is not None
        and window.contains(record_date)
    ]


def due_plan_dates(plan: Iterable[dict[str, Any]], reference: date) -> list[dict[str, Any]]:
    """Return plan days that are due as of a user's local calendar date."""

    result: list[dict[str, Any]] = []
    for workout in plan:
        workout_date = parse_local_date(workout.get("date"))
        if workout_date is not None and workout_date <= reference:
            result.append(workout)
    return sorted(result, key=lambda item: str(item.get("date", "")))
