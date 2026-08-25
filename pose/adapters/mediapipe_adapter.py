"""Optional MediaPipe adapter that converts frames to normalized NOZEERO landmarks.

The adapter is deliberately optional: the rule engines and manual workout mode
remain usable when MediaPipe is not installed or a camera frame is unreliable.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pose.models import Landmark


class PoseDependencyUnavailable(RuntimeError):
    """Raised when MediaPipe is not installed in the current runtime."""


class MediaPipePoseAdapter:
    """Small wrapper around classic or Tasks-based MediaPipe Pose APIs."""

    _LANDMARK_NAMES = (
        "nose", "left_eye_inner", "left_eye", "left_eye_outer", "right_eye_inner", "right_eye", "right_eye_outer",
        "left_ear", "right_ear", "mouth_left", "mouth_right", "left_shoulder", "right_shoulder", "left_elbow",
        "right_elbow", "left_wrist", "right_wrist", "left_pinky", "right_pinky", "left_index", "right_index",
        "left_thumb", "right_thumb", "left_hip", "right_hip", "left_knee", "right_knee", "left_ankle",
        "right_ankle", "left_heel", "right_heel", "left_foot_index", "right_foot_index",
    )

    def __init__(
        self,
        model_asset_path: str | None = None,
        model_complexity: int = 1,
        min_detection_confidence: float = 0.7,
        min_tracking_confidence: float = 0.7,
    ) -> None:
        try:
            import cv2
            import mediapipe as mp
        except ImportError as exc:
            raise PoseDependencyUnavailable("install the pose extra to enable MediaPipe") from exc
        self._cv2 = cv2
        self._mode = "classic" if hasattr(mp, "solutions") else "tasks"
        if self._mode == "classic":
            self._pose_module = mp.solutions.pose
            self._pose = self._pose_module.Pose(
                static_image_mode=False,
                model_complexity=model_complexity,
                smooth_landmarks=True,
                enable_segmentation=False,
                min_detection_confidence=min_detection_confidence,
                min_tracking_confidence=min_tracking_confidence,
            )
            return
        if not model_asset_path or not Path(model_asset_path).is_file():
            raise PoseDependencyUnavailable("MediaPipe Tasks requires a local pose_landmarker_full.task model")
        from mediapipe.tasks.python import BaseOptions, vision

        options = vision.PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=model_asset_path),
            running_mode=vision.RunningMode.IMAGE,
            num_poses=1,
            min_pose_detection_confidence=min_detection_confidence,
            min_pose_presence_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self._mp = mp
        self._pose = vision.PoseLandmarker.create_from_options(options)

    def detect(self, frame_bgr: Any) -> dict[str, Landmark]:
        rgb_frame = self._cv2.cvtColor(frame_bgr, self._cv2.COLOR_BGR2RGB)
        if self._mode == "classic":
            result = self._pose.process(rgb_frame)
            pose_landmarks = result.pose_landmarks.landmark if result.pose_landmarks else []
        else:
            image = self._mp.Image(image_format=self._mp.ImageFormat.SRGB, data=rgb_frame)
            result = self._pose.detect(image)
            pose_landmarks = result.pose_landmarks[0] if result.pose_landmarks else []
        return {
            self._LANDMARK_NAMES[index]: Landmark(
                float(landmark.x),
                float(landmark.y),
                float(getattr(landmark, "visibility", 0.0)),
            )
            for index, landmark in enumerate(pose_landmarks)
            if index < len(self._LANDMARK_NAMES)
        }

    def close(self) -> None:
        self._pose.close()


def mediapipe_available() -> bool:
    try:
        import mediapipe  # noqa: F401
    except ImportError:
        return False
    return True
