"""FastAPI application entrypoint for NOZEERO."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from backend.app.core.config import Settings, settings
from backend.app.core.errors import NozeeroError, SafetyBlockedError
from backend.app.core.logging import configure_logging
from backend.app.db.database import Database
from backend.app.repositories.sqlite_repository import SQLiteRepository
from backend.app.schemas.domain import (
    AssessmentRequest,
    AssessmentResponse,
    CoachRequest,
    CoachResponse,
    DashboardResponse,
    ExerciseResponse,
    OnboardingRequest,
    PlanRequest,
    PlanResponse,
    PoseAnalyzeRequest,
    PoseAnalyzeResponse,
    PoseCalibrationRequest,
    UserResponse,
    WellnessCheckinRequest,
    WellnessResponse,
    WellnessSummaryResponse,
    WorkoutFeedbackRequest,
    WorkoutSessionResponse,
)
from backend.app.services.application import ApplicationService, public_user
from pose.calibration.checker import calibrate_camera
from pose.counters.state_machine import RepCounter
from pose.models import CalibrationInput, Landmark
from pose.service import PoseService

logger = logging.getLogger("nozeero.api")


def _seed_if_empty(repository: SQLiteRepository) -> None:
    repository.initialize()
    if repository.list_exercises():
        return
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    exercise_path = root / "data" / "exercises" / "exercises.json"
    exercises = json.loads(exercise_path.read_text(encoding="utf-8"))
    repository.seed_exercises(exercises)


def create_app(
    repository: SQLiteRepository | None = None,
    app_settings: Settings | None = None,
    ai_service: Any | None = None,
) -> FastAPI:
    configure_logging()
    active_settings = app_settings or settings
    active_repository = repository or SQLiteRepository(Database(active_settings.database_url))
    application = ApplicationService(active_repository, active_settings, ai_service=ai_service)
    pose_service = PoseService()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        _seed_if_empty(active_repository)
        logger.info("NOZEERO API initialized with database %s", active_repository.database.database_path)
        yield

    app = FastAPI(
        title="NOZEERO API",
        version="1.0.0-alpha",
        description="Local-first, safety-first indoor training system.",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(NozeeroError)
    async def handle_domain_error(_, exc: NozeeroError) -> JSONResponse:
        status = 409 if isinstance(exc, (SafetyBlockedError, ValueError)) else 404
        return JSONResponse(status_code=status, content={"detail": str(exc)})

    @app.exception_handler(ValueError)
    async def handle_value_error(_, exc: ValueError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.get("/api/v1/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "nozeero-api", "version": app.version}

    @app.post("/api/v1/onboarding", status_code=201)
    def onboarding(request: OnboardingRequest) -> dict[str, Any]:
        return application.onboard(request)

    @app.get("/api/v1/users/{user_id}", response_model=UserResponse)
    def get_user(user_id: str) -> dict[str, Any]:
        return public_user(application.get_user_or_raise(user_id))

    @app.get("/api/v1/exercises", response_model=list[ExerciseResponse])
    def exercises(
        user_id: str | None = None,
        equipment_mode: str | None = Query(default=None),
        noise_preference: str | None = Query(default=None),
        jumping_allowed: bool | None = Query(default=None),
        available_space: str | None = Query(default=None),
    ) -> list[dict[str, Any]]:
        return application.exercises_for_user(
            user_id,
            equipment_mode=equipment_mode,
            noise_preference=noise_preference,
            jumping_allowed=jumping_allowed,
            available_space=available_space,
        )

    @app.post("/api/v1/assessments", response_model=AssessmentResponse, status_code=201)
    def assessment(request: AssessmentRequest) -> dict[str, Any]:
        return application.assess(request)

    @app.post("/api/v1/reassessments", status_code=201)
    def reassessment(request: AssessmentRequest) -> dict[str, Any]:
        return application.reassess(request)

    @app.post("/api/v1/plans", response_model=PlanResponse, status_code=201)
    def generate_plan(request: PlanRequest) -> dict[str, Any]:
        return application.generate_plan(request)

    @app.get("/api/v1/plans/current", response_model=PlanResponse | None)
    def current_plan(user_id: str) -> dict[str, Any] | None:
        return application.current_plan(user_id)

    @app.get("/api/v1/workouts/today")
    def today_workout(user_id: str, workout_date: str | None = None) -> dict[str, Any] | None:
        from datetime import date

        requested_date = date.fromisoformat(workout_date) if workout_date else None
        return application.today_workout(user_id, requested_date)

    @app.post("/api/v1/workouts/feedback", response_model=WorkoutSessionResponse, status_code=201)
    def workout_feedback(request: WorkoutFeedbackRequest) -> dict[str, Any]:
        return application.record_feedback(request)

    @app.post("/api/v1/coach", response_model=CoachResponse)
    def coach(request: CoachRequest) -> dict[str, Any]:
        source, decision = application.coach(request)
        return {"source": source, **decision}

    @app.get("/api/v1/dashboard", response_model=DashboardResponse)
    def dashboard(user_id: str) -> dict[str, Any]:
        return application.dashboard(user_id)

    @app.get("/api/v1/weekly-review")
    def weekly_review(user_id: str) -> dict[str, Any]:
        return application.weekly_review(user_id)

    @app.post("/api/v1/wellness", response_model=WellnessResponse, status_code=201)
    def wellness(request: WellnessCheckinRequest) -> dict[str, Any]:
        return application.wellness_checkin(request)

    @app.get("/api/v1/wellness/summary", response_model=WellnessSummaryResponse)
    def wellness_summary(user_id: str) -> dict[str, Any]:
        return application.wellness_summary(user_id)

    @app.get("/api/v1/users/{user_id}/data/export")
    def export_data(user_id: str) -> dict[str, Any]:
        return application.export_data(user_id)

    @app.post("/api/v1/users/{user_id}/data/reset-history", status_code=204)
    def reset_history(user_id: str) -> Response:
        application.reset_history(user_id)
        return Response(status_code=204)

    @app.delete("/api/v1/users/{user_id}/data", status_code=204)
    def delete_data(user_id: str) -> Response:
        application.delete_data(user_id)
        return Response(status_code=204)

    @app.post("/api/v1/pose/calibrate")
    def pose_calibration(request: PoseCalibrationRequest) -> dict[str, Any]:
        result = calibrate_camera(CalibrationInput(**request.model_dump()))
        return {"state": result.state, "issues": result.issues, "message": result.message}

    @app.post("/api/v1/pose/analyze", response_model=PoseAnalyzeResponse)
    def pose_analyze(request: PoseAnalyzeRequest) -> dict[str, Any]:
        landmarks = {name: Landmark(**value.model_dump()) for name, value in request.landmarks.items()}
        counter = RepCounter(request.exercise, request.reps_so_far, request.phase)
        result = pose_service.analyze(request.exercise, landmarks, counter)
        return {
            "exercise": result.exercise,
            "reps": result.reps,
            "phase": result.phase,
            "confidence": result.confidence,
            "feedback": result.feedback,
        }

    return app


app = create_app()
