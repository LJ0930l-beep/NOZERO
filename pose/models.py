"""Pose contracts shared by calibration, counters, and form rules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ConfidenceState = Literal["GOOD", "POTENTIAL_ISSUE", "UNABLE_TO_DETERMINE"]


@dataclass(frozen=True)
class Landmark:
    x: float
    y: float
    visibility: float = 1.0


@dataclass(frozen=True)
class CalibrationInput:
    full_body_visibility: float
    distance_score: float
    angle_score: float
    lighting_score: float
    occlusion_score: float
    fps: float
    pose_confidence: float


@dataclass(frozen=True)
class CalibrationResult:
    state: ConfidenceState
    issues: list[str]
    message: str


@dataclass(frozen=True)
class RepResult:
    exercise: str
    reps: int
    phase: str
    confidence: ConfidenceState
    feedback: list[str]
