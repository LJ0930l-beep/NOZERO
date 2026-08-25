from pathlib import Path

import numpy as np
import pytest

from pose.adapters.mediapipe_adapter import MediaPipePoseAdapter, PoseDependencyUnavailable


def test_missing_tasks_model_is_reported_as_optional_dependency() -> None:
    pytest.importorskip("mediapipe")
    with pytest.raises(PoseDependencyUnavailable):
        MediaPipePoseAdapter("pose/models/does-not-exist.task")


def test_tasks_adapter_handles_a_frame_without_a_detected_person() -> None:
    pytest.importorskip("mediapipe")
    pytest.importorskip("cv2")
    model_path = Path("pose/models/pose_landmarker_full.task")
    if not model_path.is_file():
        pytest.skip("download the optional MediaPipe model before running this integration test")

    adapter = MediaPipePoseAdapter(str(model_path))
    try:
        landmarks = adapter.detect(np.zeros((240, 320, 3), dtype=np.uint8))
    finally:
        adapter.close()

    assert landmarks == {}
