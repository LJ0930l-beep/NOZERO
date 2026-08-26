"""SQLite repository for persistence; engines remain storage-agnostic."""

from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import UTC, date, datetime
from typing import Any
from uuid import uuid4

from backend.app.db.database import Database


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _load(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


class SQLiteRepository:
    """Concrete repository used by the development backend."""

    def __init__(self, database: Database) -> None:
        self.database = database

    def initialize(self) -> None:
        self.database.initialize()

    def create_user(self, payload: dict[str, Any], safety_status: str) -> dict[str, Any]:
        user_id = str(uuid4())
        created_at = utc_now()
        safety = payload.get("safety", {})
        values = (
            user_id,
            created_at,
            payload["age"],
            payload["sex"],
            payload["height_cm"],
            payload["weight_kg"],
            payload["training_experience"],
            payload["available_training_days"],
            payload["session_duration_minutes"],
            payload["available_space"],
            payload["noise_preference"],
            int(payload["jumping_allowed"]),
            payload["equipment_mode"],
            payload["primary_goal"],
            payload["secondary_focus"],
            safety.get("known_medical_restrictions", ""),
            safety.get("recent_injury", ""),
            safety.get("movement_pain", ""),
            safety.get("abnormal_symptoms", ""),
            safety.get("medical_exercise_restriction", ""),
            int(bool(safety.get("exercise_chest_pain", False))),
            int(bool(safety.get("fainting_or_dizziness", False))),
            int(bool(safety.get("unusual_shortness_of_breath", False))),
            safety_status,
        )
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO users(
                    id, created_at, age, sex, height_cm, weight_kg,
                    training_experience, available_training_days,
                    session_duration_minutes, available_space, noise_preference,
                    jumping_allowed, equipment_mode, primary_goal, secondary_focus,
                    known_medical_restrictions, recent_injury, movement_pain,
                    abnormal_symptoms, medical_exercise_restriction,
                    exercise_chest_pain, fainting_or_dizziness, unusual_shortness_of_breath,
                    safety_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                values,
            )
        return self.get_user(user_id)  # type: ignore[return-value]

    def get_user(self, user_id: str) -> dict[str, Any] | None:
        with self.database.connect() as connection:
            row = connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None

    def seed_exercises(self, exercises: Iterable[dict[str, Any]]) -> int:
        count = 0
        sql = """
        INSERT OR REPLACE INTO exercises(
            id, name, name_cn, movement_pattern, primary_muscles, secondary_muscles,
            difficulty_level, equipment_modes, space_requirement, noise_level,
            impact_level, execution_type, rep_range, duration_range, recommended_sets,
            recommended_rpe, recommended_rir, regression_ids, progression_ids,
            contraindication_tags, restriction_tags, pose_supported, pose_rules, rom_rules,
            common_mistakes, coaching_cues, version, source, review_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        with self.database.connect() as connection:
            for exercise in exercises:
                connection.execute(
                    sql,
                    (
                        exercise["id"],
                        exercise["name"],
                        exercise["name_cn"],
                        exercise["movement_pattern"],
                        _dump(exercise["primary_muscles"]),
                        _dump(exercise.get("secondary_muscles", [])),
                        exercise["difficulty_level"],
                        _dump(exercise["equipment_modes"]),
                        exercise["space_requirement"],
                        exercise["noise_level"],
                        exercise["impact_level"],
                        exercise["execution_type"],
                        _dump(exercise.get("rep_range", {})),
                        _dump(exercise.get("duration_range", {})),
                        exercise.get("recommended_sets", 3),
                        exercise.get("recommended_rpe", 7),
                        exercise.get("recommended_rir", 2),
                        _dump(exercise.get("regression_ids", [])),
                        _dump(exercise.get("progression_ids", [])),
                        _dump(exercise.get("contraindication_tags", [])),
                        _dump(exercise.get("restriction_tags", [])),
                        int(exercise.get("pose_supported", False)),
                        _dump(exercise.get("pose_rules", {})),
                        _dump(exercise.get("rom_rules", {})),
                        _dump(exercise.get("common_mistakes", [])),
                        _dump(exercise.get("coaching_cues", [])),
                        exercise.get("version", "1.0.0"),
                        exercise.get("source", "NO ZERO seed"),
                        exercise.get("review_status", "REVIEWED"),
                    ),
                )
                count += 1
        return count

    def list_exercises(
        self,
        equipment_mode: str | None = None,
        noise_preference: str | None = None,
        jumping_allowed: bool | None = None,
        available_space: str | None = None,
    ) -> list[dict[str, Any]]:
        with self.database.connect() as connection:
            rows = connection.execute("SELECT * FROM exercises ORDER BY difficulty_level, name").fetchall()
        result: list[dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            item["primary_muscles"] = _load(item["primary_muscles"], [])
            item["secondary_muscles"] = _load(item["secondary_muscles"], [])
            item["equipment_modes"] = _load(item["equipment_modes"], [])
            item["rep_range"] = _load(item["rep_range"], {})
            item["duration_range"] = _load(item["duration_range"], {})
            item["regression_ids"] = _load(item["regression_ids"], [])
            item["progression_ids"] = _load(item["progression_ids"], [])
            item["contraindication_tags"] = _load(item["contraindication_tags"], [])
            item["restriction_tags"] = _load(item["restriction_tags"], [])
            item["pose_rules"] = _load(item["pose_rules"], {})
            item["rom_rules"] = _load(item.get("rom_rules"), {})
            item["common_mistakes"] = _load(item["common_mistakes"], [])
            item["coaching_cues"] = _load(item["coaching_cues"], [])
            item["pose_supported"] = bool(item["pose_supported"])
            if equipment_mode and equipment_mode not in item["equipment_modes"]:
                continue
            space_rank = {"SMALL": 1, "MEDIUM": 2, "LARGE": 3}
            if available_space and space_rank.get(item["space_requirement"], 2) > space_rank.get(available_space, 2):
                continue
            if noise_preference == "QUIET" and item["noise_level"] == "HIGH":
                continue
            if jumping_allowed is False and item["impact_level"] == "HIGH":
                continue
            result.append(item)
        return result

    def create_assessment(
        self,
        user_id: str,
        dimensions: dict[str, str],
        raw_inputs: dict[str, int],
    ) -> dict[str, Any]:
        assessment = {
            "id": str(uuid4()),
            "user_id": user_id,
            "assessed_at": utc_now(),
            "dimensions": dimensions,
            "raw_inputs": raw_inputs,
        }
        with self.database.connect() as connection:
            connection.execute(
                (
                    "INSERT INTO assessment_results(id, user_id, assessed_at, dimensions, raw_inputs) "
                    "VALUES (?, ?, ?, ?, ?)"
                ),
                (
                    assessment["id"],
                    user_id,
                    assessment["assessed_at"],
                    _dump(dimensions),
                    _dump(raw_inputs),
                ),
            )
        return assessment

    def latest_assessment(self, user_id: str) -> dict[str, Any] | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM assessment_results WHERE user_id = ? ORDER BY assessed_at DESC LIMIT 1",
                (user_id,),
            ).fetchone()
        if not row:
            return None
        item = dict(row)
        item["dimensions"] = _load(item["dimensions"], {})
        item["raw_inputs"] = _load(item["raw_inputs"], {})
        return item

    def list_assessments(self, user_id: str) -> list[dict[str, Any]]:
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM assessment_results WHERE user_id = ? ORDER BY assessed_at ASC",
                (user_id,),
            ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["dimensions"] = _load(item["dimensions"], {})
            item["raw_inputs"] = _load(item["raw_inputs"], {})
            result.append(item)
        return result

    def create_cycle(
        self,
        user_id: str,
        start_date: str,
        end_date: str,
        goal: str,
        secondary_focus: str,
        weekly_plan: list[dict[str, Any]],
        weekly_cardio_target_minutes: int = 0,
    ) -> dict[str, Any]:
        cycle = {
            "id": str(uuid4()),
            "user_id": user_id,
            "start_date": start_date,
            "end_date": end_date,
            "goal": goal,
            "secondary_focus": secondary_focus,
            "weekly_plan": weekly_plan,
            "weekly_cardio_target_minutes": weekly_cardio_target_minutes,
            "created_at": utc_now(),
        }
        with self.database.connect() as connection:
            connection.execute(
                (
                    "INSERT INTO training_cycles(id, user_id, start_date, end_date, goal, secondary_focus, "
                    "weekly_plan, created_at, weekly_cardio_target_minutes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
                ),
                (
                    cycle["id"],
                    user_id,
                    start_date,
                    end_date,
                    goal,
                    secondary_focus,
                    _dump(weekly_plan),
                    cycle["created_at"],
                    weekly_cardio_target_minutes,
                ),
            )
        return cycle

    def latest_cycle(self, user_id: str) -> dict[str, Any] | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM training_cycles WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
                (user_id,),
            ).fetchone()
        if not row:
            return None
        item = dict(row)
        item["weekly_plan"] = _load(item["weekly_plan"], [])
        item["weekly_cardio_target_minutes"] = int(item.get("weekly_cardio_target_minutes") or 0)
        return item

    def update_cycle_plan(self, cycle_id: str, weekly_plan: list[dict[str, Any]]) -> None:
        with self.database.connect() as connection:
            connection.execute(
                "UPDATE training_cycles SET weekly_plan = ? WHERE id = ?",
                (_dump(weekly_plan), cycle_id),
            )

    def seed_plan_executions(self, cycle: dict[str, Any]) -> None:
        rows = [
            (
                cycle["user_id"],
                cycle["id"],
                workout["date"],
                workout["kind"],
            )
            for workout in cycle.get("weekly_plan", [])
        ]
        if not rows:
            return
        with self.database.connect() as connection:
            connection.executemany(
                """
                INSERT OR IGNORE INTO plan_executions(user_id, cycle_id, plan_date, planned_kind, status)
                VALUES (?, ?, ?, ?, 'DUE')
                """,
                rows,
            )

    def list_plan_executions(self, user_id: str, cycle_id: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM plan_executions WHERE user_id = ?"
        params: list[Any] = [user_id]
        if cycle_id:
            query += " AND cycle_id = ?"
            params.append(cycle_id)
        query += " ORDER BY plan_date ASC"
        with self.database.connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def upsert_plan_execution(
        self,
        user_id: str,
        cycle_id: str,
        plan_date: str,
        planned_kind: str,
        status: str,
        session_id: str | None = None,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO plan_executions(
                    user_id, cycle_id, plan_date, planned_kind, status, executed_at, session_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, cycle_id, plan_date) DO UPDATE SET
                    planned_kind = excluded.planned_kind,
                    status = excluded.status,
                    executed_at = excluded.executed_at,
                    session_id = excluded.session_id
                """,
                (user_id, cycle_id, plan_date, planned_kind, status, utc_now(), session_id),
            )

    def create_session(self, payload: dict[str, Any], xp: int) -> dict[str, Any]:
        session_id = str(uuid4())
        completed_at = utc_now()
        values = (
            session_id,
            payload["user_id"],
            str(payload["workout_date"]),
            payload["status"],
            _dump(payload["workout_plan"]),
            payload.get("started_at"),
            completed_at,
            payload.get("session_rpe"),
            payload.get("rir"),
            payload.get("soreness"),
            payload.get("pain"),
            payload.get("fatigue"),
            payload.get("enjoyment"),
            payload.get("notes", ""),
            xp,
        )
        with self.database.connect() as connection:
            existing = connection.execute(
                "SELECT id FROM workout_sessions WHERE user_id = ? AND workout_date = ? "
                "ORDER BY completed_at DESC LIMIT 1",
                (payload["user_id"], str(payload["workout_date"])),
            ).fetchone()
            if existing:
                session_id = str(existing["id"])
                values = (session_id, *values[1:])
                connection.execute(
                    """
                    UPDATE workout_sessions SET status = ?, workout_plan = ?, started_at = ?,
                        completed_at = ?, session_rpe = ?, rir = ?, soreness = ?, pain = ?,
                        fatigue = ?, enjoyment = ?, notes = ?, xp = ? WHERE id = ?
                    """,
                    (
                        values[3], values[4], values[5], values[6], values[7], values[8],
                        values[9], values[10], values[11], values[12], values[13], values[14], values[0],
                    ),
                )
            else:
                connection.execute(
                    """
                    INSERT INTO workout_sessions(
                        id, user_id, workout_date, status, workout_plan, started_at,
                        completed_at, session_rpe, rir, soreness, pain, fatigue,
                        enjoyment, notes, xp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    values,
                )
        return {"id": session_id, "workout_date": str(payload["workout_date"]), "status": payload["status"], "xp": xp}

    def list_sessions(
        self,
        user_id: str,
        start_date: date | str | None = None,
        end_date: date | str | None = None,
    ) -> list[dict[str, Any]]:
        clauses = ["user_id = ?"]
        params: list[Any] = [user_id]
        if start_date is not None:
            clauses.append("workout_date >= ?")
            params.append(str(start_date))
        if end_date is not None:
            clauses.append("workout_date <= ?")
            params.append(str(end_date))
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM workout_sessions WHERE " + " AND ".join(clauses)
                + " ORDER BY workout_date ASC, completed_at ASC",
                params,
            ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["workout_plan"] = _load(item["workout_plan"], {})
            result.append(item)
        return result

    def list_progression_states(self, user_id: str) -> list[dict[str, Any]]:
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM progression_states WHERE user_id = ? ORDER BY exercise_id",
                (user_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def save_progression_state(self, state: dict[str, Any]) -> dict[str, Any]:
        values = (
            state["user_id"],
            state["exercise_id"],
            state["current_variation"],
            state.get("target_reps"),
            state.get("target_sets"),
            state.get("last_rpe"),
            state.get("last_rir"),
            state.get("decision", "MAINTAIN"),
            state.get("next_variable", "reps"),
            int(state.get("consecutive_successes", 0)),
            int(state.get("consecutive_failures", 0)),
            state.get("updated_at", utc_now()),
        )
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO progression_states(
                    user_id, exercise_id, current_variation, target_reps, target_sets,
                    last_rpe, last_rir, decision, next_variable,
                    consecutive_successes, consecutive_failures, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, exercise_id) DO UPDATE SET
                    current_variation = excluded.current_variation,
                    target_reps = excluded.target_reps,
                    target_sets = excluded.target_sets,
                    last_rpe = excluded.last_rpe,
                    last_rir = excluded.last_rir,
                    decision = excluded.decision,
                    next_variable = excluded.next_variable,
                    consecutive_successes = excluded.consecutive_successes,
                    consecutive_failures = excluded.consecutive_failures,
                    updated_at = excluded.updated_at
                """,
                values,
            )
        return dict(zip(
            (
                "user_id", "exercise_id", "current_variation", "target_reps", "target_sets",
                "last_rpe", "last_rir", "decision", "next_variable",
                "consecutive_successes", "consecutive_failures", "updated_at",
            ),
            values,
        ))

    def save_memory(self, user_id: str, memory_key: str, memory_value: str) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO fitness_memory(user_id, memory_key, memory_value, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, memory_key) DO UPDATE SET
                    memory_value = excluded.memory_value,
                    updated_at = excluded.updated_at
                """,
                (user_id, memory_key, memory_value, utc_now()),
            )

    def read_memories(self, user_id: str) -> dict[str, str]:
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT memory_key, memory_value FROM fitness_memory WHERE user_id = ?",
                (user_id,),
            ).fetchall()
        return {row["memory_key"]: row["memory_value"] for row in rows}

    def total_xp(self, user_id: str) -> int:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT COALESCE(SUM(xp), 0) AS xp FROM workout_sessions WHERE user_id = ?", (user_id,)
            ).fetchone()
        return int(row["xp"] if row else 0)

    def save_wellness(self, payload: dict[str, Any]) -> dict[str, Any]:
        log_date = str(payload["log_date"])
        values = (
            payload["user_id"],
            log_date,
            payload.get("body_weight_kg"),
            None if payload.get("protein_awareness") is None else int(payload["protein_awareness"]),
            payload.get("hydration_glasses"),
            payload.get("fruit_vegetable_servings"),
            payload.get("steps"),
            payload.get("daily_movement_minutes"),
            payload.get("sedentary_minutes"),
            payload.get("notes", ""),
        )
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO wellness_logs(
                    user_id, log_date, body_weight_kg, protein_awareness,
                    hydration_glasses, fruit_vegetable_servings, steps,
                    daily_movement_minutes, sedentary_minutes, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, log_date) DO UPDATE SET
                    body_weight_kg = excluded.body_weight_kg,
                    protein_awareness = excluded.protein_awareness,
                    hydration_glasses = excluded.hydration_glasses,
                    fruit_vegetable_servings = excluded.fruit_vegetable_servings,
                    steps = excluded.steps,
                    daily_movement_minutes = excluded.daily_movement_minutes,
                    sedentary_minutes = excluded.sedentary_minutes,
                    notes = excluded.notes
                """,
                values,
            )
        return self.get_wellness(payload["user_id"], log_date)  # type: ignore[return-value]

    def get_wellness(self, user_id: str, log_date: str) -> dict[str, Any] | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM wellness_logs WHERE user_id = ? AND log_date = ?",
                (user_id, log_date),
            ).fetchone()
        if not row:
            return None
        item = dict(row)
        if item["protein_awareness"] is not None:
            item["protein_awareness"] = bool(item["protein_awareness"])
        return item

    def list_wellness(self, user_id: str) -> list[dict[str, Any]]:
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM wellness_logs WHERE user_id = ? ORDER BY log_date ASC",
                (user_id,),
            ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            if item["protein_awareness"] is not None:
                item["protein_awareness"] = bool(item["protein_awareness"])
            result.append(item)
        return result

    def export_user_data(self, user_id: str) -> dict[str, Any]:
        latest_cycle = self.latest_cycle(user_id)
        return {
            "user": self.get_user(user_id),
            "assessments": self.list_assessments(user_id),
            "training_cycles": [latest_cycle] if latest_cycle else [],
            "workout_sessions": self.list_sessions(user_id),
            "plan_executions": self.list_plan_executions(user_id),
            "progression_states": self.list_progression_states(user_id),
            "fitness_memory": self.read_memories(user_id),
            "wellness_logs": self.list_wellness(user_id),
        }

    def reset_training_history(self, user_id: str) -> None:
        with self.database.connect() as connection:
            connection.execute("DELETE FROM workout_sessions WHERE user_id = ?", (user_id,))
            connection.execute("DELETE FROM training_cycles WHERE user_id = ?", (user_id,))
            connection.execute("DELETE FROM progression_states WHERE user_id = ?", (user_id,))
            connection.execute("DELETE FROM assessment_results WHERE user_id = ?", (user_id,))
            connection.execute("DELETE FROM fitness_memory WHERE user_id = ?", (user_id,))
            connection.execute("DELETE FROM wellness_logs WHERE user_id = ?", (user_id,))

    def delete_user(self, user_id: str) -> None:
        with self.database.connect() as connection:
            connection.execute("DELETE FROM users WHERE id = ?", (user_id,))
