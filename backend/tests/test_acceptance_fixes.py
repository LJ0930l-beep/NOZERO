import json
import sqlite3
from datetime import date, timedelta
from pathlib import Path

from backend.app.db.database import Database
from backend.app.engines.discipline.engine import plan_adherence, plan_streak
from backend.app.engines.progression.engine import update_progression_state
from backend.app.engines.safety.engine import screen_safety
from backend.app.engines.safety.restrictions import filter_exercises, resolve_restrictions
from backend.app.engines.time_windows import records_in_window
from backend.app.engines.training.engine import generate_cycle
from backend.app.engines.training.load import calculate_training_load, weekly_cardio_target
from backend.app.repositories.sqlite_repository import SQLiteRepository


def _catalog() -> list[dict]:
    return json.loads(
        (Path(__file__).resolve().parents[2] / "data" / "exercises" / "exercises.json").read_text(encoding="utf-8")
    )


def _session(workout_date: str, status: str = "FULL", exercise_id: str = "push_knee", **feedback: object) -> dict:
    return {
        "workout_date": workout_date,
        "status": status,
        "workout_plan": {
            "duration_minutes": 20,
            "blocks": [{"exercise_id": exercise_id, "sets": 3, "reps": 8, "duration_seconds": None}],
        },
        **feedback,
    }


def test_date_window_does_not_treat_last_seven_rows_as_last_seven_days() -> None:
    sessions = [
        {"workout_date": (date(2026, 8, 1) + timedelta(days=index * 5)).isoformat(), "status": "FULL"}
        for index in range(7)
    ]
    recent = records_in_window(sessions, date(2026, 8, 31), 7)
    assert len(recent) == 2
    assert {item["workout_date"] for item in recent} == {"2026-08-26", "2026-08-31"}


def test_training_load_keeps_muscle_and_pattern_exposure_independent() -> None:
    catalog = _catalog()
    sessions = [
        _session("2026-08-26", exercise_id="push_knee"),
        _session("2026-08-27", exercise_id="squat_bodyweight"),
        _session("2026-08-27", exercise_id="core_plank"),
    ]
    load = calculate_training_load(sessions, catalog, date(2026, 8, 27), 7)
    assert load.muscle_sets["chest"] == 3
    assert load.muscle_sets["quadriceps"] == 3
    assert load.muscle_sets["core"] > 0
    assert load.pattern_sets["Horizontal Push"] == 3
    assert load.pattern_sets["Squat"] == 3
    assert load.recent_pattern_sets["Squat"] == 3


def test_recent_leg_load_changes_the_next_plan_and_cardio_dose_is_goal_aware() -> None:
    profile = {
        "primary_goal": "cardio_fitness",
        "available_training_days": 3,
        "session_duration_minutes": 20,
        "jumping_allowed": False,
        "noise_preference": "QUIET",
        "training_experience": "beginner",
    }
    cycle = generate_cycle(
        profile,
        filter_exercises(_catalog(), resolve_restrictions({})),
        {"upper_body": "F2", "lower_body": "F2", "core": "F2", "cardio": "F2", "mobility": "F2"},
        date(2026, 8, 27),
        28,
        recent_load={"recent_pattern_sets": {"Squat": 6, "Lunge": 2}},
    )
    first_training = next(item for item in cycle if item["kind"] == "TRAINING")
    assert all(
        block["exercise_id"] not in {"squat_bodyweight", "squat_wall_assisted", "squat_tempo"}
        for block in first_training["blocks"]
    )
    assert first_training["phase"] == "Adaptation / Base"
    assert next(
        item for item in cycle if item["week_number"] == 2 and item["kind"] == "TRAINING"
    )["phase"] == "Progress"
    assert weekly_cardio_target({"primary_goal": "cardio_fitness"}) > weekly_cardio_target({"primary_goal": "mobility"})
    assert weekly_cardio_target(
        {"primary_goal": "cardio_fitness"}, week_index=3
    ) > weekly_cardio_target({"primary_goal": "cardio_fitness"})


def test_restriction_resolver_excludes_contraindications_and_keeps_safe_regression() -> None:
    catalog = _catalog()
    resolution = resolve_restrictions({"movement_pain": "knee pain"})
    assert "acute_knee_pain" in resolution.blocked_tags
    filtered = filter_exercises(catalog, resolution)
    ids = {item["id"] for item in filtered}
    assert "squat_bodyweight" not in ids
    assert "squat_wall_assisted" in ids
    assert screen_safety({"movement_pain": "none", "abnormal_symptoms": "否"}).status == "SAFE"


def test_progression_requires_two_quality_sessions_and_ignores_one_abnormal_outlier() -> None:
    exercise = next(item for item in _catalog() if item["id"] == "push_knee")
    good = [_session("2026-08-25", session_rpe=7, rir=2, pain=0), _session("2026-08-26", session_rpe=7, rir=2, pain=0)]
    progressed = update_progression_state("u1", exercise, good)
    assert progressed["decision"] == "PROGRESS"
    assert progressed["target_reps"] == 9

    one_outlier = [*good[:1], _session("2026-08-26", status="FULL", session_rpe=10, rir=0, pain=0)]
    maintained = update_progression_state("u1", exercise, one_outlier, progressed)
    assert maintained["decision"] == "MAINTAIN"
    assert maintained["current_variation"] == progressed["current_variation"]


def test_plan_adherence_counts_due_recovery_days_without_session_rows() -> None:
    plan = [
        {
            "date": (date(2026, 8, 24) + timedelta(days=index)).isoformat(),
            "kind": "TRAINING" if index < 3 else "RECOVERY",
        }
        for index in range(7)
    ]
    executions = [
        {"plan_date": plan[index]["date"], "status": "FULL"}
        for index in range(3)
    ]
    adherence = plan_adherence(plan, executions, date(2026, 8, 30))
    assert adherence["completed"] == 7
    assert adherence["planned"] == 7
    assert adherence["percentage"] == 100.0
    assert plan_streak(plan, executions, date(2026, 8, 30)) == (7, 7)

    executions[1]["status"] = "ZERO"
    missed = plan_adherence(plan, executions, date(2026, 8, 30))
    assert missed["completed"] == 6
    assert missed["percentage"] == round(6 / 7 * 100, 1)


def test_old_schema_migrates_additively_and_preserves_user_data(tmp_path: Path) -> None:
    db_path = tmp_path / "old.db"
    connection = sqlite3.connect(db_path)
    connection.executescript(
        """
        CREATE TABLE users (
            id TEXT PRIMARY KEY, created_at TEXT NOT NULL, age INTEGER NOT NULL, sex TEXT NOT NULL,
            height_cm REAL NOT NULL, weight_kg REAL NOT NULL, training_experience TEXT NOT NULL,
            available_training_days INTEGER NOT NULL, session_duration_minutes INTEGER NOT NULL,
            available_space TEXT NOT NULL, noise_preference TEXT NOT NULL, jumping_allowed INTEGER NOT NULL,
            equipment_mode TEXT NOT NULL, primary_goal TEXT NOT NULL, secondary_focus TEXT NOT NULL,
            known_medical_restrictions TEXT NOT NULL DEFAULT '', recent_injury TEXT NOT NULL DEFAULT '',
            movement_pain TEXT NOT NULL DEFAULT '', abnormal_symptoms TEXT NOT NULL DEFAULT '',
            medical_exercise_restriction TEXT NOT NULL DEFAULT '', safety_status TEXT NOT NULL DEFAULT 'PENDING'
        );
        CREATE TABLE exercises (
            id TEXT PRIMARY KEY, name TEXT NOT NULL, name_cn TEXT NOT NULL, movement_pattern TEXT NOT NULL,
            primary_muscles TEXT NOT NULL, secondary_muscles TEXT NOT NULL, difficulty_level INTEGER NOT NULL,
            equipment_modes TEXT NOT NULL, space_requirement TEXT NOT NULL, noise_level TEXT NOT NULL,
            impact_level TEXT NOT NULL, execution_type TEXT NOT NULL, rep_range TEXT NOT NULL,
            duration_range TEXT NOT NULL, recommended_sets INTEGER NOT NULL, recommended_rpe REAL NOT NULL,
            recommended_rir REAL NOT NULL, regression_ids TEXT NOT NULL, progression_ids TEXT NOT NULL,
            contraindication_tags TEXT NOT NULL, restriction_tags TEXT NOT NULL, pose_supported INTEGER NOT NULL,
            pose_rules TEXT NOT NULL, common_mistakes TEXT NOT NULL, coaching_cues TEXT NOT NULL,
            version TEXT NOT NULL, source TEXT NOT NULL, review_status TEXT NOT NULL
        );
        CREATE TABLE training_cycles (
            id TEXT PRIMARY KEY, user_id TEXT NOT NULL, start_date TEXT NOT NULL, end_date TEXT NOT NULL,
            goal TEXT NOT NULL, secondary_focus TEXT NOT NULL, weekly_plan TEXT NOT NULL, created_at TEXT NOT NULL
        );
        INSERT INTO users VALUES ('legacy', '2026-08-01T00:00:00+00:00', 30, 'x', 170, 70, 'beginner', 3, 20,
            'SMALL', 'QUIET', 0, 'ZERO', 'strength', 'full_body', '', '', '', '', '', 'SAFE');
        """
    )
    connection.commit()
    connection.close()

    database = Database(f"sqlite:///{db_path}")
    repository = SQLiteRepository(database)
    repository.initialize()
    with database.connect() as migrated:
        version = migrated.execute("SELECT schema_version FROM schema_meta WHERE id = 1").fetchone()[0]
        user_columns = {row[1] for row in migrated.execute("PRAGMA table_info(users)").fetchall()}
        tables = {row[0] for row in migrated.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()}
    assert version == 2
    assert "legacy" == repository.get_user("legacy")["id"]
    assert {"exercise_chest_pain", "fainting_or_dizziness", "unusual_shortness_of_breath"} <= user_columns
    assert {"progression_states", "plan_executions"} <= tables
