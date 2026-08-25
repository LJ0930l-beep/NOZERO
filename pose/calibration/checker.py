"""Reject unreliable camera conditions instead of fabricating form feedback."""

from __future__ import annotations

from pose.models import CalibrationInput, CalibrationResult


def calibrate_camera(values: CalibrationInput) -> CalibrationResult:
    issues: list[str] = []
    if values.full_body_visibility < 0.85:
        issues.append("full body is not visible")
    if values.distance_score < 0.7:
        issues.append("move the camera farther away or frame the body")
    if values.angle_score < 0.7:
        issues.append("use a clearer side or front angle")
    if values.lighting_score < 0.6:
        issues.append("increase lighting")
    if values.occlusion_score < 0.75:
        issues.append("remove occlusion")
    if values.fps < 15:
        issues.append("camera FPS is too low")
    if values.pose_confidence < 0.7:
        issues.append("pose confidence is too low")
    if issues:
        state = (
            "UNABLE_TO_DETERMINE"
            if values.pose_confidence < 0.5 or values.full_body_visibility < 0.5
            else "POTENTIAL_ISSUE"
        )
        return CalibrationResult(state, issues, "当前无法可靠判断；请调整摄像头后再试。")
    return CalibrationResult("GOOD", [], "摄像头条件满足基础动作分析要求。")
