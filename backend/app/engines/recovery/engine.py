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
    muscle_group_exposure_minutes: int = 0,
    training_frequency: int = 0,
    completion_rate: float = 1.0,
    enjoyment: int | None = None,
    muscle_group_exposure: dict[str, float] | None = None,
    pattern_exposure: dict[str, float] | None = None,
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
    if completion_rate < 0.5 and (soreness_value >= 6 or fatigue_value >= 6):
        return RecoveryResult(
            "REDUCED",
            "low completion combined with fatigue or soreness suggests the dose is not sustainable",
            "reduce the next dose and preserve the highest-value movement pattern",
        )
    if soreness_value >= 6 or fatigue_value >= 6 or (session_rpe is not None and session_rpe >= 9):
        return RecoveryResult(
            "SWAP_FOCUS",
            "moderate fatigue or soreness suggests changing emphasis",
            "train a fresh pattern or use a short session",
        )
    if enjoyment is not None and enjoyment <= 2 and fatigue_value >= 4:
        return RecoveryResult(
            "SWAP_FOCUS",
            "low enjoyment with fatigue suggests a friction or recovery problem",
            "change focus and use a lower-friction short session",
        )
    if weekly_volume_minutes >= 240:
        return RecoveryResult("REDUCED", "recent weekly volume is high", "cap the next session and prioritize recovery")
    if pattern_exposure and max(pattern_exposure.values(), default=0) >= 8:
        return RecoveryResult(
            "REDUCED",
            "one movement pattern has high recent exposure",
            "change emphasis and avoid repeating the highest-loaded pattern",
        )
    if muscle_group_exposure and max(muscle_group_exposure.values(), default=0) >= 12:
        return RecoveryResult(
            "REDUCED",
            "one muscle group has high recent set exposure",
            "reduce the next dose for the most-exposed muscle group",
        )
    if muscle_group_exposure_minutes >= 120 and training_frequency >= 3:
        return RecoveryResult(
            "REDUCED",
            "recent muscle-group exposure and frequency are high",
            "swap focus and cap exposure before adding more work",
        )
    if training_frequency >= 6:
        return RecoveryResult(
            "REDUCED",
            "training frequency is high across the recent window",
            "protect a recovery day before the next hard session",
        )
    return RecoveryResult(
        "NORMAL", "no recovery signal exceeds the conservative threshold", "continue the planned session"
    )
