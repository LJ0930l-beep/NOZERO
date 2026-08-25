from pose.calibration.checker import calibrate_camera
from pose.counters.state_machine import RepCounter, update_squat
from pose.models import CalibrationInput, Landmark


def _squat_sample(knee_angle: float, visibility: float = 1.0):
    # The exact geometry is supplied to the angle function through points; use a simple
    # visibility case here to verify the confidence contract without camera files.
    return {
        "left_hip": Landmark(0.4, 0.2, visibility),
        "left_knee": Landmark(0.4, 0.5, visibility),
        "left_ankle": Landmark(0.4, 0.8, visibility),
        "right_hip": Landmark(0.6, 0.2, visibility),
        "right_knee": Landmark(0.6, 0.5, visibility),
        "right_ankle": Landmark(0.6, 0.8, visibility),
    }


def test_calibration_returns_unable_when_camera_is_bad() -> None:
    result = calibrate_camera(CalibrationInput(0.4, 0.5, 0.5, 0.4, 0.4, 10, 0.3))
    assert result.state == "UNABLE_TO_DETERMINE"


def test_counter_admits_low_visibility() -> None:
    result = update_squat(RepCounter("squat"), _squat_sample(90, visibility=0.2))
    assert result.confidence == "UNABLE_TO_DETERMINE"
