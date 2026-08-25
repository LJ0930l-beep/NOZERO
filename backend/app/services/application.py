"""Use-case orchestration for the API; business decisions stay in engines."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from ai.ollama.client import OllamaClient
from ai.ollama.service import LocalAIService
from backend.app.core.config import Settings
from backend.app.core.errors import ResourceNotFoundError, SafetyBlockedError
from backend.app.engines.assessment.engine import assess_dimensions
from backend.app.engines.discipline.engine import consistency, discipline_level, streaks, xp_for_status
from backend.app.engines.recovery.engine import assess_recovery
from backend.app.engines.safety.engine import screen_safety
from backend.app.engines.training.engine import generate_cycle
from backend.app.repositories.sqlite_repository import SQLiteRepository
from backend.app.schemas.domain import (
    AssessmentRequest,
    CoachRequest,
    OnboardingRequest,
    PlanRequest,
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
        }
        return result

    def get_user_or_raise(self, user_id: str) -> dict[str, Any]:
        row = self.repository.get_user(user_id)
        if not row:
            raise ResourceNotFoundError(f"user {user_id} not found")
        return row

    def exercises_for_user(self, user_id: str | None = None, **filters: Any) -> list[dict[str, Any]]:
        if user_id:
            user = self.get_user_or_raise(user_id)
            filters = {
                "equipment_mode": user["equipment_mode"],
                "noise_preference": user["noise_preference"],
                "jumping_allowed": bool(user["jumping_allowed"]),
                "available_space": user["available_space"],
            }
        return self.repository.list_exercises(**filters)

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
        return {"assessment": current, "changes": changes, "next_action": "update plan from the new dimensions"}

    def generate_plan(self, request: PlanRequest) -> dict[str, Any]:
        user = self.get_user_or_raise(request.user_id)
        if user["safety_status"] == "BLOCKED":
            raise SafetyBlockedError("safety screening blocks normal plan generation")
        assessment = self.repository.latest_assessment(request.user_id)
        if not assessment:
            raise ValueError("complete the multidimensional assessment before generating a plan")
        start = request.start_date or date.today()
        exercises = self.exercises_for_user(request.user_id)
        weekly_plan = generate_cycle(
            profile=user,
            exercises=exercises,
            assessment=assessment["dimensions"],
            start_date=start,
            cycle_days=request.cycle_days,
        )
        return self.repository.create_cycle(
            request.user_id,
            start.isoformat(),
            (start + timedelta(days=request.cycle_days - 1)).isoformat(),
            user["primary_goal"],
            user["secondary_focus"],
            weekly_plan,
        )

    def current_plan(self, user_id: str) -> dict[str, Any] | None:
        self.get_user_or_raise(user_id)
        return self.repository.latest_cycle(user_id)

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
        weekly_volume = sum(
            int(item.get("workout_plan", {}).get("duration_minutes", 0))
            for item in recent[-7:]
            if isinstance(item.get("workout_plan"), dict)
        )
        recovery = assess_recovery(request.soreness, request.pain, request.fatigue, request.session_rpe, weekly_volume)
        status = request.status
        if request.pain is not None and request.pain >= 4:
            status = "RECOVERY"
        if recovery.status == "RECOVERY" and status == "FULL":
            status = "RECOVERY"
        xp = xp_for_status(status)
        payload = request.model_dump()
        payload["status"] = status
        session = self.repository.create_session(payload, xp)
        if request.fatigue is not None:
            self.repository.save_memory(request.user_id, "fatigue_pattern", f"last={request.fatigue}/10")
        if request.enjoyment is not None:
            self.repository.save_memory(
                request.user_id, "training_preference", f"last_enjoyment={request.enjoyment}/10"
            )
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
        current_streak, longest_streak = streaks(sessions)
        assessment = self.repository.latest_assessment(user_id)
        levels = (
            assessment["dimensions"]
            if assessment
            else {"upper_body": "F1", "lower_body": "F1", "core": "F1", "cardio": "F1", "mobility": "F1"}
        )
        total_minutes = sum(
            int(item.get("workout_plan", {}).get("duration_minutes", 0))
            for item in sessions
            if isinstance(item.get("workout_plan"), dict)
        )
        return {
            "user": public_user(user),
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "consistency": consistency(sessions),
            "total_training_minutes": total_minutes,
            "fitness_levels": levels,
            "discipline_level": discipline_level(self.repository.total_xp(user_id)),
            "xp": self.repository.total_xp(user_id),
            "next_workout": self.today_workout(user_id),
        }

    def weekly_review(self, user_id: str) -> dict[str, Any]:
        self.get_user_or_raise(user_id)
        sessions = self.repository.list_sessions(user_id)[-7:]
        successful = [item for item in sessions if item.get("status") in {"FULL", "MINIMUM", "RECOVERY"}]
        total_minutes = sum(
            int(item.get("workout_plan", {}).get("duration_minutes", 0))
            for item in sessions
            if isinstance(item.get("workout_plan"), dict)
        )
        return {
            "sessions_completed": len(successful),
            "consistency": round(len(successful) / 7 * 100, 1),
            "training_time_minutes": total_minutes,
            "full_days": sum(item.get("status") == "FULL" for item in sessions),
            "minimum_days": sum(item.get("status") == "MINIMUM" for item in sessions),
            "recovery_days": sum(item.get("status") == "RECOVERY" for item in sessions),
            "zero_days": sum(item.get("status") == "ZERO" for item in sessions),
            "next_week_recommendation": "keep the plan and adjust one variable from recent recovery feedback",
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
