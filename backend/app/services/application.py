"""Use-case orchestration for the API; business decisions stay in engines."""

from __future__ import annotations

from datetime import date, timedelta
from statistics import mean
from typing import Any

from ai.memory.manager import MemoryManager
from ai.ollama.client import OllamaClient
from ai.ollama.review import WeeklyReview
from ai.ollama.service import LocalAIService
from backend.app.core.config import Settings
from backend.app.core.errors import ResourceNotFoundError, SafetyBlockedError
from backend.app.engines.assessment.engine import assess_dimensions
from backend.app.engines.discipline.engine import (
    achievements,
    consistency,
    discipline_level,
    plan_adherence,
    plan_streak,
    streaks,
    xp_for_status,
)
from backend.app.engines.progression.engine import (
    apply_progression_states_to_plan,
    update_progression_state,
)
from backend.app.engines.recovery.engine import assess_recovery
from backend.app.engines.safety.engine import screen_safety
from backend.app.engines.safety.restrictions import filter_exercises, resolve_restrictions
from backend.app.engines.time_windows import parse_local_date, records_in_window
from backend.app.engines.training.engine import build_minimum_workout, build_short_workout, generate_cycle
from backend.app.engines.training.load import aerobic_dose, calculate_training_load, weekly_cardio_target
from backend.app.repositories.sqlite_repository import SQLiteRepository, utc_now
from backend.app.schemas.domain import (
    AssessmentRequest,
    CoachRequest,
    OnboardingRequest,
    PlanRequest,
    WellnessCheckinRequest,
    WorkoutFeedbackRequest,
)


def public_user(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "age": row["age"],
        "sex": row["sex"],
        "height_cm": row["height_cm"],
        "weight_kg": row["weight_kg"],
        "training_experience": row["training_experience"],
        "available_training_days": row["available_training_days"],
        "session_duration_minutes": row["session_duration_minutes"],
        "available_space": row["available_space"],
        "noise_preference": row["noise_preference"],
        "jumping_allowed": bool(row["jumping_allowed"]),
        "equipment_mode": row["equipment_mode"],
        "primary_goal": row["primary_goal"],
        "secondary_focus": row["secondary_focus"],
        "safety": {
            "known_medical_restrictions": row["known_medical_restrictions"],
            "recent_injury": row["recent_injury"],
            "movement_pain": row["movement_pain"],
            "abnormal_symptoms": row["abnormal_symptoms"],
            "medical_exercise_restriction": row["medical_exercise_restriction"],
            "exercise_chest_pain": bool(row.get("exercise_chest_pain", 0)),
            "fainting_or_dizziness": bool(row.get("fainting_or_dizziness", 0)),
            "unusual_shortness_of_breath": bool(row.get("unusual_shortness_of_breath", 0)),
        },
        "safety_status": row["safety_status"],
    }


class ApplicationService:
    def __init__(
        self, repository: SQLiteRepository, settings: Settings, ai_service: LocalAIService | None = None
    ) -> None:
        self.repository = repository
        self.settings = settings
        self.ai_service = ai_service or LocalAIService(
            OllamaClient(settings.ollama_base_url, settings.ollama_model, settings.ollama_timeout_seconds),
            allow_model=True,
        )

    def onboard(self, request: OnboardingRequest) -> dict[str, Any]:
        safety_payload = request.safety.model_dump()
        safety_result = screen_safety(safety_payload)
        row = self.repository.create_user(request.model_dump(), safety_result.status)
        result = public_user(row)
        result["safety_result"] = {
            "status": safety_result.status,
            "blockers": safety_result.blockers,
            "cautions": safety_result.cautions,
            "recommended_action": safety_result.recommended_action,
            "blocked_tags": safety_result.blocked_tags,
            "caution_tags": safety_result.caution_tags,
        }
        return result

    def get_user_or_raise(self, user_id: str) -> dict[str, Any]:
        row = self.repository.get_user(user_id)
        if not row:
            raise ResourceNotFoundError(f"user {user_id} not found")
        return row

    def _settle_recovery_days(self, cycle: dict[str, Any], reference: date) -> None:
        """Materialize due planned recovery without inventing a workout session."""

        executions = self.repository.list_plan_executions(cycle["user_id"], cycle["id"])
        status_by_date = {str(item.get("plan_date")): str(item.get("status")) for item in executions}
        for workout in cycle.get("weekly_plan", []):
            workout_date = parse_local_date(workout.get("date"))
            if workout_date is None or workout_date > reference or workout.get("kind") != "RECOVERY":
                continue
            if status_by_date.get(str(workout.get("date"))) in {None, "DUE"}:
                self.repository.upsert_plan_execution(
                    cycle["user_id"],
                    cycle["id"],
                    str(workout["date"]),
                    "RECOVERY",
                    "RECOVERY",
                )

    @staticmethod
    def _selected_workout_plan(request: WorkoutFeedbackRequest, status: str) -> dict[str, Any]:
        """Persist the dose actually executed, not the unmodified full plan."""

        plan = dict(request.workout_plan)
        if status == "MINIMUM" and isinstance(plan.get("minimum_workout"), list):
            plan["blocks"] = plan["minimum_workout"]
            plan["duration_minutes"] = min(int(plan.get("duration_minutes") or 0), 6)
        elif status == "RECOVERY" and plan.get("kind") != "RECOVERY":
            plan["blocks"] = []
            plan["duration_minutes"] = 0
        return plan

    def _refresh_progression(self, user_id: str, workout_plan: dict[str, Any], after_date: str) -> None:
        catalog = self.repository.list_exercises()
        exercise_lookup = {str(item["id"]): item for item in catalog}
        sessions = self.repository.list_sessions(user_id)
        existing = {str(item["exercise_id"]): item for item in self.repository.list_progression_states(user_id)}
        blocks = workout_plan.get("blocks") if isinstance(workout_plan.get("blocks"), list) else []
        for block in blocks:
            if not isinstance(block, dict):
                continue
            exercise_id = str(block.get("exercise_id"))
            exercise = exercise_lookup.get(exercise_id)
            if not exercise:
                continue
            state = update_progression_state(user_id, exercise, sessions, existing.get(exercise_id))
            state["updated_at"] = utc_now()
            existing[exercise_id] = self.repository.save_progression_state(state)
        cycle = self.repository.latest_cycle(user_id)
        if cycle and existing:
            updated_plan = apply_progression_states_to_plan(
                cycle.get("weekly_plan", []), existing, exercise_lookup, after_date
            )
            for workout in updated_plan:
                if workout.get("kind") == "TRAINING":
                    workout["short_workout"] = build_short_workout(workout, 3)
                    workout["minimum_workout"] = build_minimum_workout(workout, 2)
            self.repository.update_cycle_plan(cycle["id"], updated_plan)

    def exercises_for_user(self, user_id: str | None = None, **filters: Any) -> list[dict[str, Any]]:
        resolution = None
        if user_id:
            user = self.get_user_or_raise(user_id)
            filters = {
                "equipment_mode": user["equipment_mode"],
                "noise_preference": user["noise_preference"],
                "jumping_allowed": bool(user["jumping_allowed"]),
                "available_space": user["available_space"],
            }
            resolution = resolve_restrictions(
                {
                    "known_medical_restrictions": user["known_medical_restrictions"],
                    "recent_injury": user["recent_injury"],
                    "movement_pain": user["movement_pain"],
                    "abnormal_symptoms": user["abnormal_symptoms"],
                    "medical_exercise_restriction": user["medical_exercise_restriction"],
                    "exercise_chest_pain": bool(user.get("exercise_chest_pain", 0)),
                    "fainting_or_dizziness": bool(user.get("fainting_or_dizziness", 0)),
                    "unusual_shortness_of_breath": bool(user.get("unusual_shortness_of_breath", 0)),
                }
            )
        exercises = self.repository.list_exercises(**filters)
        return filter_exercises(exercises, resolution) if resolution else exercises

    def assess(self, request: AssessmentRequest) -> dict[str, Any]:
        self.get_user_or_raise(request.user_id)
        raw = {
            "push_up_reps": request.push_up_reps,
            "squat_reps": request.squat_reps,
            "plank_seconds": request.plank_seconds,
            "cardio_minutes": request.cardio_minutes,
            "mobility_score": request.mobility_score,
        }
        return self.repository.create_assessment(request.user_id, assess_dimensions(raw), raw)

    def reassess(self, request: AssessmentRequest) -> dict[str, Any]:
        previous = self.repository.latest_assessment(request.user_id)
        current = self.assess(request)
        previous_dimensions = previous["dimensions"] if previous else {}
        changes: dict[str, dict[str, str | int]] = {}
        for key, current_level in current["dimensions"].items():
            before = previous_dimensions.get(key, "F1")
            changes[key] = {
                "before": before,
                "after": current_level,
                "delta": int(current_level[1]) - int(before[1]),
            }
        updated_plan = None
        if self.repository.latest_cycle(request.user_id):
            updated_plan = self.generate_plan(PlanRequest(user_id=request.user_id, cycle_days=28))
        return {
            "assessment": current,
            "changes": changes,
            "plan": updated_plan,
            "next_action": (
                "updated the current plan from the new dimensions"
                if updated_plan
                else "generate a plan from the new dimensions"
            ),
        }

    def generate_plan(self, request: PlanRequest) -> dict[str, Any]:
        user = self.get_user_or_raise(request.user_id)
        if user["safety_status"] == "BLOCKED":
            raise SafetyBlockedError("safety screening blocks normal plan generation")
        assessment = self.repository.latest_assessment(request.user_id)
        if not assessment:
            raise ValueError("complete the multidimensional assessment before generating a plan")
        start = request.start_date or date.today()
        exercises = self.exercises_for_user(request.user_id)
        all_sessions = self.repository.list_sessions(request.user_id)
        recent_sessions = records_in_window(all_sessions, start, 90)
        catalog = self.repository.list_exercises()
        wellness_logs = self.repository.list_wellness(request.user_id)
        load = calculate_training_load(recent_sessions, catalog, start, 7, wellness_logs)
        recent_7 = records_in_window(recent_sessions, start, 7)
        successful_dates = {
            parse_local_date(item.get("workout_date"))
            for item in recent_7
            if item.get("status") in {"FULL", "MINIMUM", "RECOVERY"}
        }
        successful_dates.discard(None)
        latest_session = recent_7[-1] if recent_7 else {}
        recovery = assess_recovery(
            latest_session.get("soreness"),
            latest_session.get("pain"),
            latest_session.get("fatigue"),
            latest_session.get("session_rpe"),
            int(load.total_training_minutes),
            muscle_group_exposure_minutes=0,
            training_frequency=len(successful_dates),
            completion_rate=1.0 if latest_session.get("status") in {"FULL", "RECOVERY"} else 0.5,
            enjoyment=latest_session.get("enjoyment"),
            muscle_group_exposure=load.muscle_sets,
            pattern_exposure=load.recent_pattern_sets,
        )
        progression_states = {
            str(item["exercise_id"]): item for item in self.repository.list_progression_states(request.user_id)
        }
        weekly_plan = generate_cycle(
            profile=user,
            exercises=exercises,
            assessment=assessment["dimensions"],
            start_date=start,
            cycle_days=request.cycle_days,
            recent_sessions=recent_sessions,
            recovery_status=recovery.status,
            recent_load=load.as_dict(),
            progression_states=progression_states,
        )
        cycle = self.repository.create_cycle(
            request.user_id,
            start.isoformat(),
            (start + timedelta(days=request.cycle_days - 1)).isoformat(),
            user["primary_goal"],
            user["secondary_focus"],
            weekly_plan,
            weekly_cardio_target(user, assessment["dimensions"], 0),
        )
        self.repository.seed_plan_executions(cycle)
        cycle["cardio_minutes_completed"] = round(load.cardio_minutes + load.daily_movement_minutes, 1)
        return cycle

    def current_plan(self, user_id: str) -> dict[str, Any] | None:
        self.get_user_or_raise(user_id)
        cycle = self.repository.latest_cycle(user_id)
        if not cycle:
            return None
        self.repository.seed_plan_executions(cycle)
        self._settle_recovery_days(cycle, date.today())
        catalog = self.repository.list_exercises()
        load = calculate_training_load(
            self.repository.list_sessions(user_id),
            catalog,
            date.today(),
            7,
            self.repository.list_wellness(user_id),
        )
        cycle["cardio_minutes_completed"] = round(load.cardio_minutes + load.daily_movement_minutes, 1)
        return cycle

    def today_workout(self, user_id: str, requested_date: date | None = None) -> dict[str, Any] | None:
        cycle = self.current_plan(user_id)
        if not cycle:
            return None
        target = (requested_date or date.today()).isoformat()
        for workout in cycle["weekly_plan"]:
            if workout["date"] == target:
                return workout
        return cycle["weekly_plan"][0] if cycle["weekly_plan"] else None

    def record_feedback(self, request: WorkoutFeedbackRequest) -> dict[str, Any]:
        self.get_user_or_raise(request.user_id)
        recent = self.repository.list_sessions(request.user_id)
        catalog = self.repository.list_exercises()
        recent_window = records_in_window(recent, request.workout_date, 7)
        load = calculate_training_load(
            recent,
            catalog,
            request.workout_date,
            7,
            self.repository.list_wellness(request.user_id),
        )
        successful_dates = {
            parse_local_date(item.get("workout_date"))
            for item in recent_window
            if item.get("status") in {"FULL", "MINIMUM", "RECOVERY"}
        }
        successful_dates.discard(None)
        recovery = assess_recovery(
            request.soreness,
            request.pain,
            request.fatigue,
            request.session_rpe,
            int(load.total_training_minutes),
            muscle_group_exposure_minutes=0,
            training_frequency=len(successful_dates),
            completion_rate={"FULL": 1.0, "MINIMUM": 0.5, "RECOVERY": 1.0, "ZERO": 0.0}.get(request.status, 0.0),
            enjoyment=request.enjoyment,
            muscle_group_exposure=load.muscle_sets,
            pattern_exposure=load.recent_pattern_sets,
        )
        status = request.status
        if request.pain is not None and request.pain >= 4:
            status = "RECOVERY"
        if recovery.status == "RECOVERY" and status == "FULL":
            status = "RECOVERY"
        xp = xp_for_status(status)
        payload = request.model_dump()
        payload["status"] = status
        payload["workout_plan"] = self._selected_workout_plan(request, status)
        session = self.repository.create_session(payload, xp)
        cycle = self.repository.latest_cycle(request.user_id)
        if cycle:
            workout = next(
                (item for item in cycle.get("weekly_plan", []) if item.get("date") == request.workout_date.isoformat()),
                None,
            )
            if workout:
                self.repository.upsert_plan_execution(
                    request.user_id,
                    cycle["id"],
                    request.workout_date.isoformat(),
                    workout.get("kind", "TRAINING"),
                    status,
                    session["id"],
                )
        self._refresh_progression(request.user_id, payload["workout_plan"], request.workout_date.isoformat())
        memory_updates = MemoryManager.select_updates(
            {
                "fatigue_pattern": f"last={request.fatigue}/10" if request.fatigue is not None else None,
                "training_preference": (
                    f"last_enjoyment={request.enjoyment}/10" if request.enjoyment is not None else None
                ),
            }
        )
        for key, value in memory_updates.items():
            self.repository.save_memory(request.user_id, key, value)
        recommendation = recovery.suggested_action
        return {**session, "next_recommendation": recommendation, "recovery_status": recovery.status}

    def coach(self, request: CoachRequest) -> tuple[str, dict[str, Any]]:
        user = self.get_user_or_raise(request.user_id)
        today = self.today_workout(request.user_id)
        sessions = self.repository.list_sessions(request.user_id)
        last = sessions[-1] if sessions else {}
        recovery = assess_recovery(last.get("soreness"), last.get("pain"), last.get("fatigue"), last.get("session_rpe"))
        source, decision = self.ai_service.coach(
            request.message,
            user,
            today,
            sessions,
            recovery.status,
            self.repository.read_memories(request.user_id),
            user["safety_status"],
        )
        return source, decision.model_dump()

    def dashboard(self, user_id: str) -> dict[str, Any]:
        user = self.get_user_or_raise(user_id)
        sessions = self.repository.list_sessions(user_id)
        assessments = self.repository.list_assessments(user_id)
        today = date.today()
        cycle = self.current_plan(user_id)
        executions = self.repository.list_plan_executions(user_id, cycle["id"] if cycle else None)
        if cycle:
            current_streak, longest_streak = plan_streak(cycle["weekly_plan"], executions, today)
            adherence = plan_adherence(cycle["weekly_plan"], executions, today)
        else:
            current_streak, longest_streak = streaks(sessions, today)
            adherence = {"completed": 0, "planned": 0, "percentage": 0.0, "recovery_days": 0, "zero_days": 0}
        assessment = self.repository.latest_assessment(user_id)
        levels = (
            assessment["dimensions"]
            if assessment
            else {"upper_body": "F1", "lower_body": "F1", "core": "F1", "cardio": "F1", "mobility": "F1"}
        )
        total_minutes = sum(
            int(item.get("workout_plan", {}).get("duration_minutes", 0))
            for item in sessions
            if item.get("status") in {"FULL", "MINIMUM", "RECOVERY"}
            and isinstance(item.get("workout_plan"), dict)
        )
        return {
            "user": public_user(user),
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "consistency": consistency(sessions, today),
            "activity_consistency": consistency(sessions, today),
            "total_training_minutes": total_minutes,
            "fitness_levels": levels,
            "assessment_history": assessments,
            "performance_change": WeeklyReview.compare_assessments(assessments),
            "discipline_level": discipline_level(self.repository.total_xp(user_id)),
            "achievements": achievements(sessions, self.repository.total_xp(user_id)),
            "xp": self.repository.total_xp(user_id),
            "next_workout": self.today_workout(user_id, today),
            "plan_adherence": adherence,
            "aerobic_dose": aerobic_dose(
                calculate_training_load(
                    sessions,
                    self.repository.list_exercises(),
                    today,
                    7,
                    self.repository.list_wellness(user_id),
                ),
                int(cycle.get("weekly_cardio_target_minutes", 0)) if cycle else 0,
            ),
        }

    def weekly_review(self, user_id: str) -> dict[str, Any]:
        self.get_user_or_raise(user_id)
        sessions = self.repository.list_sessions(user_id)
        metrics = WeeklyReview.summarize(sessions, self.repository.list_assessments(user_id), date.today())
        next_recommendation = "progress one variable from recent quality completion"
        if metrics["recovery_days"] or metrics["minimum_days"] > metrics["full_days"]:
            next_recommendation = "keep the plan conservative and protect recovery before adding volume"
        return {
            **metrics,
            "next_week_recommendation": next_recommendation,
        }

    def export_data(self, user_id: str) -> dict[str, Any]:
        self.get_user_or_raise(user_id)
        return self.repository.export_user_data(user_id)

    def reset_history(self, user_id: str) -> None:
        self.get_user_or_raise(user_id)
        self.repository.reset_training_history(user_id)

    def delete_data(self, user_id: str) -> None:
        self.get_user_or_raise(user_id)
        self.repository.delete_user(user_id)

    def wellness_checkin(self, request: WellnessCheckinRequest) -> dict[str, Any]:
        self.get_user_or_raise(request.user_id)
        payload = request.model_dump()
        payload["log_date"] = (request.log_date or date.today()).isoformat()
        return self.repository.save_wellness(payload)

    def wellness_summary(self, user_id: str) -> dict[str, Any]:
        self.get_user_or_raise(user_id)
        logs = self.repository.list_wellness(user_id)
        latest = logs[-1] if logs else None
        trend = [
            {"date": item["log_date"], "weight_kg": item["body_weight_kg"]}
            for item in logs
            if item.get("body_weight_kg") is not None
        ]
        averages: dict[str, float] = {}
        numeric_fields = (
            "steps",
            "daily_movement_minutes",
            "sedentary_minutes",
            "hydration_glasses",
            "fruit_vegetable_servings",
        )
        for field in numeric_fields:
            values = [float(item[field]) for item in logs if item.get(field) is not None]
            if values:
                averages[field] = round(mean(values), 1)
        protein_values = [
            float(item["protein_awareness"])
            for item in logs
            if item.get("protein_awareness") is not None
        ]
        if protein_values:
            averages["protein_awareness_rate"] = round(mean(protein_values) * 100, 1)
        return {"latest": latest, "body_weight_trend": trend, "averages": averages}
