"""SQLite adapter with a stable seam for a future PostgreSQL repository."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    age INTEGER NOT NULL,
    sex TEXT NOT NULL,
    height_cm REAL NOT NULL,
    weight_kg REAL NOT NULL,
    training_experience TEXT NOT NULL,
    available_training_days INTEGER NOT NULL,
    session_duration_minutes INTEGER NOT NULL,
    available_space TEXT NOT NULL,
    noise_preference TEXT NOT NULL,
    jumping_allowed INTEGER NOT NULL,
    equipment_mode TEXT NOT NULL,
    primary_goal TEXT NOT NULL,
    secondary_focus TEXT NOT NULL,
    known_medical_restrictions TEXT NOT NULL DEFAULT '',
    recent_injury TEXT NOT NULL DEFAULT '',
    movement_pain TEXT NOT NULL DEFAULT '',
    abnormal_symptoms TEXT NOT NULL DEFAULT '',
    medical_exercise_restriction TEXT NOT NULL DEFAULT '',
    safety_status TEXT NOT NULL DEFAULT 'PENDING'
);

CREATE TABLE IF NOT EXISTS exercises (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    name_cn TEXT NOT NULL,
    movement_pattern TEXT NOT NULL,
    primary_muscles TEXT NOT NULL,
    secondary_muscles TEXT NOT NULL,
    difficulty_level INTEGER NOT NULL,
    equipment_modes TEXT NOT NULL,
    space_requirement TEXT NOT NULL,
    noise_level TEXT NOT NULL,
    impact_level TEXT NOT NULL,
    execution_type TEXT NOT NULL,
    rep_range TEXT NOT NULL,
    duration_range TEXT NOT NULL,
    recommended_sets INTEGER NOT NULL,
    recommended_rpe REAL NOT NULL,
    recommended_rir REAL NOT NULL,
    regression_ids TEXT NOT NULL,
    progression_ids TEXT NOT NULL,
    contraindication_tags TEXT NOT NULL,
    restriction_tags TEXT NOT NULL,
    pose_supported INTEGER NOT NULL,
    pose_rules TEXT NOT NULL,
    rom_rules TEXT NOT NULL,
    common_mistakes TEXT NOT NULL,
    coaching_cues TEXT NOT NULL,
    version TEXT NOT NULL,
    source TEXT NOT NULL,
    review_status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS assessment_results (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    assessed_at TEXT NOT NULL,
    dimensions TEXT NOT NULL,
    raw_inputs TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS training_cycles (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    goal TEXT NOT NULL,
    secondary_focus TEXT NOT NULL,
    weekly_plan TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS workout_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    workout_date TEXT NOT NULL,
    status TEXT NOT NULL,
    workout_plan TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    session_rpe REAL,
    rir REAL,
    soreness INTEGER,
    pain INTEGER,
    fatigue INTEGER,
    enjoyment INTEGER,
    notes TEXT NOT NULL DEFAULT '',
    xp INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS fitness_memory (
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    memory_key TEXT NOT NULL,
    memory_value TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (user_id, memory_key)
);

CREATE TABLE IF NOT EXISTS wellness_logs (
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    log_date TEXT NOT NULL,
    body_weight_kg REAL,
    protein_awareness INTEGER,
    hydration_glasses INTEGER,
    fruit_vegetable_servings INTEGER,
    steps INTEGER,
    daily_movement_minutes INTEGER,
    sedentary_minutes INTEGER,
    notes TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (user_id, log_date)
);

CREATE INDEX IF NOT EXISTS idx_assessments_user_date
    ON assessment_results(user_id, assessed_at);
CREATE INDEX IF NOT EXISTS idx_cycles_user_date
    ON training_cycles(user_id, start_date);
CREATE INDEX IF NOT EXISTS idx_sessions_user_date
    ON workout_sessions(user_id, workout_date);
CREATE INDEX IF NOT EXISTS idx_wellness_user_date
    ON wellness_logs(user_id, log_date);
"""


class Database:
    """Connection factory that keeps SQLite details out of business engines."""

    def __init__(self, database_url: str) -> None:
        self.database_path = self._resolve_path(database_url)
        self._memory_connection: sqlite3.Connection | None = None
        if self.database_path != Path(":memory:"):
            self.database_path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _resolve_path(database_url: str) -> Path:
        if database_url == ":memory:" or database_url == "sqlite:///:memory:":
            return Path(":memory:")
        prefix = "sqlite:///"
        raw_path = database_url[len(prefix) :] if database_url.startswith(prefix) else database_url
        path = Path(raw_path)
        return path if path.is_absolute() else Path.cwd() / path

    def connect(self) -> sqlite3.Connection:
        if self.database_path == Path(":memory:"):
            if self._memory_connection is None:
                self._memory_connection = sqlite3.connect(":memory:", check_same_thread=False)
            connection = self._memory_connection
        else:
            connection = sqlite3.connect(str(self.database_path), check_same_thread=False)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(SCHEMA)
            columns = {row[1] for row in connection.execute("PRAGMA table_info(exercises)").fetchall()}
            if "rom_rules" not in columns:
                connection.execute("ALTER TABLE exercises ADD COLUMN rom_rules TEXT NOT NULL DEFAULT '{}'")

    def session(self) -> Iterator[sqlite3.Connection]:
        connection = self.connect()
        try:
            yield connection
        finally:
            if self.database_path != Path(":memory:"):
                connection.close()
