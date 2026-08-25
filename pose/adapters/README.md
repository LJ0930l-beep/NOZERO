# Vision adapter

`MediaPipePoseAdapter` is the optional local frame adapter. It accepts an OpenCV BGR frame, performs local MediaPipe Pose inference, and returns normalized landmarks for the existing confidence-aware counters. It never writes the input frame. If MediaPipe is absent, the application must keep Manual Mode available and report that pose cannot be determined.
