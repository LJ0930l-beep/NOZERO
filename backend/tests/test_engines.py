import json
from datetime import date
from pathlib import Path

from backend.app.engines.assessment.engine import assess_dimensions
from backend.app.engines.discipline.engine import achievements, consistency, streaks, xp_for_status
from backend.app.engines.progression.engine import decide_progression
from backend.app.engines.recovery.engine import assess_recovery
from backend.app.engines.safety.engine import screen_safety
from backend.app.engines.training.engine import build_minimum_workout, build_short_workout, generate_cycle


def test_safety_blocks_red_flags_but_handles_negated_blank_values() -> None:
    assert screen_safety({"abnormal_symptoms": "没有胸痛", "movement_pain": "无"}).status == "SAFE"
    result = screen_safety({"abnormal_symptoms": "I have chest pain when exercising"})
    assert result.status == "BLOCKED"
    assert "chest pain" in result.blockers


def test_assessment_is_multidimensional() -> None:
    dimensions = assess_dimensions(
        {"push_up_reps": 12, "squat_reps": 28, "plank_seconds": 55, "cardio_minutes": 18, "mobility_score": 70}
    )
    assert set(dimensions) == {"upper_body", "lower_body", "core", "cardio", "mobility"}
    assert dimensions["upper_body"] == "F3"


def test_progression_has_progress_maintain_and_regress_paths() -> None:
    assert decide_progression(0.95, 7, 2, 0.9, "NORMAL", 2).decision == "PROGRESS"
    assert decide_progression(0.82, 8.5, 1, 0.75, "NORMAL", 2).decision == "MAINTAIN"
    assert decide_progression(0.5, 9.5, 0, 0.5, "NORMAL", 2).decision == "REGRESS"
    assert "tempo" in decide_progression(0.95, 7, 2, 0.9, "NORMAL", 2, tempo_quality=0.9).next_step


def test_recovery_escalates_pain_and_high_fatigue() -> None:
    assert assess_recovery(2, 5, 4, 7).status == "RECOVERY"
    assert assess_recovery(8, 0, 8, 8).status == "REDUCED"
    assert assess_recovery(1, 0, 2, 6).status == "NORMAL"
    assert assess_recovery(0, 0, 1, 6, 90, muscle_group_exposure_minutes=120, training_frequency=3).status == "REDUCED"
    assert assess_recovery(1, 0, 7, 8, completion_rate=0.4).status == "REDUCED"
    assert assess_recovery(1, 0, 5, 7, enjoyment=2).status == "SWAP_FOCUS"


def test_recovery_day_counts_as_streak_and_zero_does_not() -> None:
    sessions = [
        {"workout_date": "2026-08-20", "status": "FULL"},
        {"workout_date": "2026-08-21", "status": "RECOVERY"},
        {"workout_date": "2026-08-22", "status": "MINIMUM"},
        {"workout_date": "2026-08-23", "status": "ZERO"},
    ]
    assert streaks(sessions, date(2026, 8, 23)) == (0, 3)
    assert consistency(sessions, date(2026, 8, 23))["7"]["completed"] == 3
    assert xp_for_status("RECOVERY") == 20
    assert "recovery_is_training" in achievements(sessions, 120)


def test_goal_profiles_change_structure_and_minimum_derives_from_plan() -> None:
    exercises = [
        {
            "id": "sq",
            "name": "Squat",
            "movement_pattern": "Squat",
            "noise_level": "LOW",
            "impact_level": "LOW",
            "execution_type": "reps",
            "rep_range": {"min": 8, "max": 15},
            "duration_range": {},
            "coaching_cues": ["brace"],
        },
        {
            "id": "push",
            "name": "Push",
            "movement_pattern": "Horizontal Push",
            "noise_level": "LOW",
            "impact_level": "LOW",
            "execution_type": "reps",
            "rep_range": {"min": 5, "max": 12},
            "duration_range": {},
            "coaching_cues": ["control"],
        },
        {
            "id": "core",
            "name": "Plank",
            "movement_pattern": "Anti Extension",
            "noise_level": "LOW",
            "impact_level": "LOW",
            "execution_type": "duration",
            "rep_range": {},
            "duration_range": {"min": 20, "max": 60},
            "coaching_cues": ["breathe"],
        },
        {
            "id": "cardio_marching",
            "name": "March",
            "movement_pattern": "Cardio",
            "noise_level": "LOW",
            "impact_level": "LOW",
            "execution_type": "duration",
            "rep_range": {},
            "duration_range": {"min": 30, "max": 90},
            "coaching_cues": ["smooth"],
        },
    ]
    profile = {
        "primary_goal": "fat_loss",
        "available_training_days": 4,
        "session_duration_minutes": 20,
        "jumping_allowed": False,
        "noise_preference": "QUIET",
        "training_experience": "beginner",
    }
    fat_loss = generate_cycle(profile, exercises, None, date(2026, 8, 24), 7)
    profile["primary_goal"] = "build_exercise_habit"
    habit = generate_cycle(profile, exercises, None, date(2026, 8, 24), 7)
    assert sum(day["kind"] == "TRAINING" for day in fat_loss) >= sum(day["kind"] == "TRAINING" for day in habit)
    training_day = next(day for day in fat_loss if day["kind"] == "TRAINING")
    minimum = build_minimum_workout(training_day)
    assert minimum and all(block["sets"] == 1 for block in minimum)
    short = build_short_workout(training_day)
    assert short and len(short) >= len(minimum)
    assert all(
        short_block["sets"] <= full_block["sets"]
        for short_block, full_block in zip(short, training_day["blocks"])
    )


def test_assessment_level_changes_variation_without_llm_generation() -> None:
    catalog = json.loads(
        (Path(__file__).resolve().parents[2] / "data" / "exercises" / "exercises.json").read_text(encoding="utf-8")
    )
    profile = {
        "primary_goal": "strength",
        "available_training_days": 4,
        "session_duration_minutes": 30,
        "jumping_allowed": False,
        "noise_preference": "QUIET",
        "training_experience": "intermediate",
    }
    low = generate_cycle(
        profile,
        catalog,
        {"upper_body": "F1", "lower_body": "F1", "core": "F1", "cardio": "F1", "mobility": "F1"},
        date(2026, 8, 24),
        7,
    )
    high = generate_cycle(
        profile,
        catalog,
        {"upper_body": "F5", "lower_body": "F5", "core": "F5", "cardio": "F5", "mobility": "F5"},
        date(2026, 8, 24),
        7,
    )
    low_squat = next(day for day in low if day["kind"] == "TRAINING")["blocks"][0]["exercise_id"]
    high_squat = next(day for day in high if day["kind"] == "TRAINING")["blocks"][0]["exercise_id"]
    assert low_squat == "squat_wall_assisted"
    assert high_squat == "squat_tempo"
