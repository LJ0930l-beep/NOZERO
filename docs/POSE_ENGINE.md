# Pose Engine

The pose boundary is modular: calibration, detector/geometry, counter, form rules, and confidence management. Calibration checks full-body visibility, camera distance, angle, lighting, occlusion, FPS, and pose confidence. Anything below the conservative threshold returns `POTENTIAL_ISSUE` or `UNABLE_TO_DETERMINE`.

The current V1 primitive supports normalized-landmark squat and push-up phase counters and basic explainable form feedback. `pose.adapters.mediapipe_adapter` provides a local OpenCV/MediaPipe bridge when the `pose` extra and the official model asset are installed. Run `python scripts/download_pose_model.py` to obtain the ignored model asset. Manual mode is always available, and the adapter returns no landmarks when MediaPipe cannot determine a pose.

Raw video is not stored or uploaded by the backend contract.
