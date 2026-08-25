"""Seek-safe phase counters for squat and push-up landmark samples."""

from __future__ import annotations

from dataclasses import dataclass

from pose.detectors.geometry import angle, average_visibility
from pose.models import Landmark, RepResult


@dataclass
class RepCounter:
    exercise: str
    reps: int = 0
    phase: str = "UP"

    def update(self, down: bool, up: bool, confidence_ok: bool) -> RepResult:
        if not confidence_ok:
            return RepResult(
                self.exercise,
                self.reps,
                self.phase,
                "UNABLE_TO_DETERMINE",
                ["当前无法可靠判断，请调整镜头或保持身体完整可见。"],
            )
        if down and self.phase == "UP":
            self.phase = "DOWN"
        elif up and self.phase == "DOWN":
            self.phase = "UP"
            self.reps += 1
        return RepResult(self.exercise, self.reps, self.phase, "GOOD", [])


def update_squat(counter: RepCounter, landmarks: dict[str, Landmark]) -> RepResult:
    names = ["left_hip", "left_knee", "left_ankle", "right_hip", "right_knee", "right_ankle"]
    if any(name not in landmarks for name in names):
        return counter.update(False, False, False)
    confidence_ok = average_visibility(landmarks, names) >= 0.7
    if not confidence_ok:
        return counter.update(False, False, False)
    left_angle = angle(landmarks["left_hip"], landmarks["left_knee"], landmarks["left_ankle"])
    right_angle = angle(landmarks["right_hip"], landmarks["right_knee"], landmarks["right_ankle"])
    knee_angle = (left_angle + right_angle) / 2
    return counter.update(down=knee_angle < 115, up=knee_angle > 155, confidence_ok=True)


def update_pushup(counter: RepCounter, landmarks: dict[str, Landmark]) -> RepResult:
    names = ["left_shoulder", "left_elbow", "left_wrist", "right_shoulder", "right_elbow", "right_wrist"]
    if any(name not in landmarks for name in names):
        return counter.update(False, False, False)
    confidence_ok = average_visibility(landmarks, names) >= 0.7
    if not confidence_ok:
        return counter.update(False, False, False)
    left_angle = angle(landmarks["left_shoulder"], landmarks["left_elbow"], landmarks["left_wrist"])
    right_angle = angle(landmarks["right_shoulder"], landmarks["right_elbow"], landmarks["right_wrist"])
    elbow_angle = (left_angle + right_angle) / 2
    return counter.update(down=elbow_angle < 100, up=elbow_angle > 155, confidence_ok=True)
