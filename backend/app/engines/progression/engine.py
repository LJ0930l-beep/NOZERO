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
) -> ProgressionDecision:
    if recovery_status == "RECOVERY" or form_quality < 0.6:
        return ProgressionDecision(
            "REGRESS", "recovery or form quality is below the safe threshold", "reduce leverage, range, or volume"
        )
    if completion_rate < 0.75 or (rpe is not None and rpe >= 9.5) or (rir is not None and rir < 0.5):
        return ProgressionDecision(
            "REGRESS",
            "completion or effort indicates the current dose is too demanding",
            "reduce one variable before adding load",
        )
    if completion_rate >= 0.9 and form_quality >= 0.8 and (rpe is None or rpe <= 8.0) and (rir is None or rir >= 1.0):
        if current_difficulty >= 5:
            return ProgressionDecision(
                "PROGRESS", "quality completion at the top difficulty", "progress tempo, ROM, or density"
            )
        return ProgressionDecision(
            "PROGRESS",
            "quality completion with reserve",
            "move to the next safe progression or add a small set/repetition step",
        )
    return ProgressionDecision(
        "MAINTAIN",
        "evidence is mixed or insufficient for a change",
        "repeat the current variation and collect another session",
    )
