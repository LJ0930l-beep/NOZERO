"""Evidence-based progression decisions independent of AI."""

from __future__ import annotations

from dataclasses import dataclass


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
