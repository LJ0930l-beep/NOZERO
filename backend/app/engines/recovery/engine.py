"""Recovery decisions from user feedback and recent training load."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RecoveryResult:
    status: str
    reason: str
    suggested_action: str


def assess_recovery(
    soreness: int | None,
    pain: int | None,
    fatigue: int | None,
    session_rpe: float | None,
    weekly_volume_minutes: int = 0,
) -> RecoveryResult:
    pain_value = pain or 0
    soreness_value = soreness or 0
    fatigue_value = fatigue or 0
    if pain_value >= 4:
        return RecoveryResult(
            "RECOVERY",
            "reported pain is above the conservative threshold",
            "stop painful movements and use recovery or professional guidance",
        )
    if pain_value >= 2 or soreness_value >= 8 or fatigue_value >= 8:
        return RecoveryResult(
            "REDUCED", "pain, soreness, or fatigue is high", "reduce volume and avoid the affected movement pattern"
        )
    if soreness_value >= 6 or fatigue_value >= 6 or (session_rpe is not None and session_rpe >= 9):
        return RecoveryResult(
            "SWAP_FOCUS",
            "moderate fatigue or soreness suggests changing emphasis",
            "train a fresh pattern or use a short session",
        )
    if weekly_volume_minutes >= 240:
        return RecoveryResult("REDUCED", "recent weekly volume is high", "cap the next session and prioritize recovery")
    return RecoveryResult(
        "NORMAL", "no recovery signal exceeds the conservative threshold", "continue the planned session"
    )
