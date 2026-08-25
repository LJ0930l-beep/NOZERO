"""Download the official MediaPipe Pose Landmarker model into the ignored cache."""

from __future__ import annotations

import argparse
from pathlib import Path
from urllib.request import urlopen

MODEL_URL = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/1/pose_landmarker_full.task"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("pose/models/pose_landmarker_full.task"))
    args = parser.parse_args()
    output = args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    with urlopen(MODEL_URL, timeout=60) as response:
        output.write_bytes(response.read())
    print(f"Downloaded MediaPipe model to {output.resolve()}")


if __name__ == "__main__":
    main()
