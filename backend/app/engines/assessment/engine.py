"""Dimension-level assessment that avoids one coarse beginner label."""

from __future__ import annotations


def _level(value: float, thresholds: tuple[float, float, float, float]) -> str:
    if value < thresholds[0]:
        return "F1"
    if value < thresholds[1]:
        return "F2"
    if value < thresholds[2]:
        return "F3"
    if value < thresholds[3]:
        return "F4"
    return "F5"


def assess_dimensions(inputs: dict[str, int]) -> dict[str, str]:
    return {
        "upper_body": _level(inputs["push_up_reps"], (3, 8, 15, 25)),
        "lower_body": _level(inputs["squat_reps"], (10, 20, 35, 55)),
        "core": _level(inputs["plank_seconds"], (20, 40, 75, 120)),
        "cardio": _level(inputs["cardio_minutes"], (5, 12, 25, 45)),
        "mobility": _level(inputs["mobility_score"], (25, 45, 65, 85)),
    }


def average_fitness_level(dimensions: dict[str, str]) -> str:
    values = [int(level[1]) for level in dimensions.values() if level.startswith("F")]
    if not values:
        return "F1"
    return f"F{round(sum(values) / len(values))}"
