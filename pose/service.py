"""Pose service facade for normalized landmarks from manual or local adapters."""

from __future__ import annotations

from pose.calibration.checker import calibrate_camera
from pose.counters.state_machine import RepCounter, update_pushup, update_squat
from pose.form_rules.basic import pushup_feedback, squat_feedback
from pose.models import CalibrationInput, Landmark, RepResult


class PoseService:
    def calibrate(self, values: CalibrationInput):
        return calibrate_camera(values)

    def analyze(self, exercise: str, landmarks: dict[str, Landmark], counter: RepCounter) -> RepResult:
        if exercise == "squat":
            result = update_squat(counter, landmarks)
            state, feedback = squat_feedback(landmarks)
        elif exercise == "push_up":
            result = update_pushup(counter, landmarks)
            state, feedback = pushup_feedback(landmarks)
        else:
            return RepResult(
                exercise, counter.reps, counter.phase, "UNABLE_TO_DETERMINE", ["该动作尚未进入可靠的 V1 识别范围。"]
            )
        if result.confidence == "UNABLE_TO_DETERMINE":
            return result
        return RepResult(result.exercise, result.reps, result.phase, state, feedback)
