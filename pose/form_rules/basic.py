"""Basic, explainable form checks for the first two supported exercises."""

from __future__ import annotations

from pose.models import ConfidenceState, Landmark


def squat_feedback(landmarks: dict[str, Landmark]) -> tuple[ConfidenceState, list[str]]:
    required = ["left_hip", "left_knee", "left_ankle", "right_hip", "right_knee", "right_ankle"]
    if any(name not in landmarks or landmarks[name].visibility < 0.7 for name in required):
        return "UNABLE_TO_DETERMINE", ["当前无法可靠判断下肢轨迹。"]
    feedback: list[str] = []
    if abs(landmarks["left_knee"].x - landmarks["left_ankle"].x) > 0.18:
        feedback.append("保持膝盖与脚尖方向更一致。")
    if abs(landmarks["right_knee"].x - landmarks["right_ankle"].x) > 0.18:
        feedback.append("保持膝盖与脚尖方向更一致。")
    return ("POTENTIAL_ISSUE" if feedback else "GOOD"), feedback


def pushup_feedback(landmarks: dict[str, Landmark]) -> tuple[ConfidenceState, list[str]]:
    required = ["left_shoulder", "left_hip", "left_ankle", "right_shoulder", "right_hip", "right_ankle"]
    if any(name not in landmarks or landmarks[name].visibility < 0.7 for name in required):
        return "UNABLE_TO_DETERMINE", ["当前无法可靠判断身体对齐。"]
    shoulder_y = (landmarks["left_shoulder"].y + landmarks["right_shoulder"].y) / 2
    hip_y = (landmarks["left_hip"].y + landmarks["right_hip"].y) / 2
    ankle_y = (landmarks["left_ankle"].y + landmarks["right_ankle"].y) / 2
    if hip_y - shoulder_y > 0.18 or ankle_y - hip_y > 0.25:
        return "POTENTIAL_ISSUE", ["尝试保持肩、髋、脚踝在更稳定的直线上。"]
    return "GOOD", []
