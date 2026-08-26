from fastapi.testclient import TestClient

from backend.app.core.config import Settings
from backend.app.db.database import Database
from backend.app.main import create_app
from backend.app.repositories.sqlite_repository import SQLiteRepository


def _client() -> TestClient:
    settings = Settings(database_url="sqlite:///:memory:", ollama_timeout_seconds=0.1)
    repository = SQLiteRepository(Database(settings.database_url))
    return TestClient(create_app(repository=repository, app_settings=settings))


def test_core_flow_onboards_assesses_plans_and_records_feedback() -> None:
    with _client() as client:
        assert client.get("/api/v1/health").json()["status"] == "ok"
        onboarding = client.post(
            "/api/v1/onboarding",
            json={
                "age": 31,
                "sex": "prefer_not_to_say",
                "height_cm": 170,
                "weight_kg": 70,
                "training_experience": "beginner",
                "available_training_days": 3,
                "session_duration_minutes": 20,
                "available_space": "SMALL",
                "noise_preference": "QUIET",
                "jumping_allowed": False,
                "equipment_mode": "ZERO",
                "primary_goal": "fat_loss",
                "secondary_focus": "abs",
                "safety": {},
            },
        )
        assert onboarding.status_code == 201
        user_id = onboarding.json()["id"]
        assert onboarding.json()["safety_result"]["status"] == "SAFE"
        assert len(client.get(f"/api/v1/exercises?user_id={user_id}").json()) > 0
        assessment = client.post(
            "/api/v1/assessments",
            json={
                "user_id": user_id,
                "push_up_reps": 8,
                "squat_reps": 20,
                "plank_seconds": 45,
                "cardio_minutes": 12,
                "mobility_score": 60,
            },
        )
        assert assessment.status_code == 201
        plan = client.post("/api/v1/plans", json={"user_id": user_id, "cycle_days": 7})
        assert plan.status_code == 201
        workout = plan.json()["weekly_plan"][0]
        assert workout["short_workout"]
        assert workout["minimum_workout"]
        feedback = client.post(
            "/api/v1/workouts/feedback",
            json={
                "user_id": user_id,
                "workout_date": workout["date"],
                "status": "FULL",
                "workout_plan": workout,
                "session_rpe": 7,
                "rir": 2,
                "soreness": 1,
                "pain": 0,
                "fatigue": 3,
                "enjoyment": 8,
                "notes": "steady",
            },
        )
        assert feedback.status_code == 201
        assert feedback.json()["xp"] == 100
        dashboard = client.get(f"/api/v1/dashboard?user_id={user_id}")
        assert dashboard.status_code == 200
        assert dashboard.json()["xp"] == 100


def test_safety_override_blocks_plan_and_coach_does_not_override() -> None:
    with _client() as client:
        onboarding = client.post(
            "/api/v1/onboarding",
            json={
                "age": 31,
                "sex": "x",
                "height_cm": 170,
                "weight_kg": 70,
                "training_experience": "beginner",
                "available_training_days": 3,
                "session_duration_minutes": 20,
                "available_space": "SMALL",
                "noise_preference": "NORMAL",
                "jumping_allowed": True,
                "equipment_mode": "ZERO",
                "primary_goal": "strength",
                "secondary_focus": "full_body",
                "safety": {"abnormal_symptoms": "I have chest pain when exercising"},
            },
        )
        user_id = onboarding.json()["id"]
        assert onboarding.json()["safety_result"]["status"] == "BLOCKED"
        assert client.post("/api/v1/plans", json={"user_id": user_id, "cycle_days": 7}).status_code == 409
        coach = client.post("/api/v1/coach", json={"user_id": user_id, "message": "我胸痛但想坚持训练"})
        assert coach.status_code == 200
        assert coach.json()["recommendation"] == "stop"


def test_pose_endpoint_admits_uncertainty() -> None:
    with _client() as client:
        response = client.post(
            "/api/v1/pose/analyze",
            json={
                "exercise": "squat",
                "landmarks": {"left_hip": {"x": 0.5, "y": 0.4, "visibility": 0.2}},
                "reps_so_far": 0,
            },
        )
        assert response.status_code == 200
        assert response.json()["confidence"] == "UNABLE_TO_DETERMINE"


def test_reassessment_and_local_data_controls() -> None:
    with _client() as client:
        onboarding = client.post(
            "/api/v1/onboarding",
            json={
                "age": 28, "sex": "x", "height_cm": 168, "weight_kg": 64,
                "training_experience": "new", "available_training_days": 2, "session_duration_minutes": 15,
                "available_space": "SMALL", "noise_preference": "QUIET", "jumping_allowed": False,
                "equipment_mode": "ZERO", "primary_goal": "build_exercise_habit", "secondary_focus": "full_body",
                "safety": {},
            },
        )
        user_id = onboarding.json()["id"]
        first = {
            "user_id": user_id,
            "push_up_reps": 3,
            "squat_reps": 12,
            "plank_seconds": 25,
            "cardio_minutes": 8,
            "mobility_score": 45,
        }
        assert client.post("/api/v1/assessments", json=first).status_code == 201
        assert client.post("/api/v1/plans", json={"user_id": user_id, "cycle_days": 28}).status_code == 201
        second = {**first, "push_up_reps": 12, "plank_seconds": 60}
        reassessment = client.post("/api/v1/reassessments", json=second)
        assert reassessment.status_code == 201
        assert reassessment.json()["changes"]["upper_body"]["delta"] > 0
        assert reassessment.json()["plan"]["weekly_plan"]
        exported = client.get(f"/api/v1/users/{user_id}/data/export")
        assert exported.status_code == 200
        assert len(exported.json()["assessments"]) == 2
        assert client.post(f"/api/v1/users/{user_id}/data/reset-history").status_code == 204
        assert client.get(f"/api/v1/users/{user_id}/data/export").json()["assessments"] == []


def test_pull_is_explicitly_equipment_limited_and_wellness_is_local() -> None:
    with _client() as client:
        base = {
            "age": 35, "sex": "x", "height_cm": 175, "weight_kg": 75,
            "training_experience": "intermediate", "available_training_days": 4, "session_duration_minutes": 30,
            "available_space": "MEDIUM", "noise_preference": "NORMAL", "jumping_allowed": True,
            "primary_goal": "muscle_gain", "secondary_focus": "back", "safety": {},
        }
        zero = client.post("/api/v1/onboarding", json={**base, "equipment_mode": "ZERO"}).json()["id"]
        zero_exercises = client.get(f"/api/v1/exercises?user_id={zero}").json()
        assert not any(item["movement_pattern"] == "Pull" for item in zero_exercises)
        minimal = client.post("/api/v1/onboarding", json={**base, "equipment_mode": "MINIMAL"}).json()["id"]
        minimal_exercises = client.get(f"/api/v1/exercises?user_id={minimal}").json()
        assert any(item["movement_pattern"] == "Pull" for item in minimal_exercises)
        wellness = client.post(
            "/api/v1/wellness",
            json={
                "user_id": minimal,
                "log_date": "2026-08-26",
                "body_weight_kg": 74.5,
                "protein_awareness": True,
                "hydration_glasses": 7,
                "fruit_vegetable_servings": 4,
                "steps": 8000,
                "daily_movement_minutes": 45,
                "sedentary_minutes": 420,
            },
        )
        assert wellness.status_code == 201
        summary = client.get(f"/api/v1/wellness/summary?user_id={minimal}").json()
        assert summary["body_weight_trend"][0]["weight_kg"] == 74.5
        assert summary["averages"]["steps"] == 8000
        assert client.get(f"/api/v1/users/{minimal}/data/export").json()["wellness_logs"]


def test_real_call_chain_persists_plan_adherence_and_progression_state() -> None:
    with _client() as client:
        onboarding = client.post(
            "/api/v1/onboarding",
            json={
                "age": 32, "sex": "x", "height_cm": 170, "weight_kg": 70,
                "training_experience": "beginner", "available_training_days": 3, "session_duration_minutes": 20,
                "available_space": "SMALL", "noise_preference": "QUIET", "jumping_allowed": False,
                "equipment_mode": "ZERO", "primary_goal": "strength", "secondary_focus": "full_body", "safety": {},
            },
        )
        user_id = onboarding.json()["id"]
        assessment = {
            "user_id": user_id, "push_up_reps": 8, "squat_reps": 20, "plank_seconds": 45,
            "cardio_minutes": 12, "mobility_score": 60,
        }
        assert client.post("/api/v1/assessments", json=assessment).status_code == 201
        plan = client.post(
            "/api/v1/plans",
            json={"user_id": user_id, "cycle_days": 7, "start_date": "2026-08-24"},
        ).json()
        training_days = [item for item in plan["weekly_plan"] if item["kind"] == "TRAINING"]
        for workout in training_days:
            response = client.post(
                "/api/v1/workouts/feedback",
                json={
                    "user_id": user_id, "workout_date": workout["date"], "status": "FULL",
                    "workout_plan": workout, "session_rpe": 7, "rir": 2, "soreness": 1,
                    "pain": 0, "fatigue": 2, "enjoyment": 8,
                },
            )
            assert response.status_code == 201
        dashboard = client.get(f"/api/v1/dashboard?user_id={user_id}").json()
        assert dashboard["plan_adherence"]["planned"] == 4
        assert dashboard["plan_adherence"]["completed"] == 4
        assert dashboard["plan_adherence"]["percentage"] == 100.0
        exported = client.get(f"/api/v1/users/{user_id}/data/export").json()
        assert len(exported["progression_states"]) >= 1
        assert len(exported["plan_executions"]) == 7
