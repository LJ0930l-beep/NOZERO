# Pose Engine

The pose boundary is modular: calibration, detector/geometry, counter, form rules, and confidence management. Calibration checks full-body visibility, camera distance, angle, lighting, occlusion, FPS, and pose confidence. Anything below the conservative threshold returns `POTENTIAL_ISSUE` or `UNABLE_TO_DETERMINE`.

The current V1 primitive supports normalized-landmark squat and push-up phase counters and basic explainable form feedback. Manual mode is always available. Browser MediaPipe/OpenCV capture is intentionally not claimed as complete until the camera adapter, calibration UX, and representative lighting/occlusion fixtures are integrated.

Raw video is not stored or uploaded by the backend contract.
