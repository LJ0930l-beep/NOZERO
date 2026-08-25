"""Dependency-free normalized landmark geometry."""

from __future__ import annotations

import math

from pose.models import Landmark


def angle(a: Landmark, b: Landmark, c: Landmark) -> float:
    ab = (a.x - b.x, a.y - b.y)
    cb = (c.x - b.x, c.y - b.y)
    denominator = math.hypot(*ab) * math.hypot(*cb)
    if denominator == 0:
        return 0.0
    cosine = max(-1.0, min(1.0, (ab[0] * cb[0] + ab[1] * cb[1]) / denominator))
    return math.degrees(math.acos(cosine))


def average_visibility(landmarks: dict[str, Landmark], names: list[str]) -> float:
    visible = [landmarks[name].visibility for name in names if name in landmarks]
    return sum(visible) / len(visible) if visible else 0.0
