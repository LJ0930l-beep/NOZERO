"""API schemas shared by routes and deterministic domain engines."""

from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field

EquipmentMode = Literal["ZERO", "HOME", "MINIMAL"]
NoisePreference = Literal["QUIET", "NORMAL"]
Goal = Literal[
    "fat_loss",
    "abs",
    "muscle_gain",
    "body_shaping",
    "strength",
    "cardio_fitness",
    "core_strength",
    "mobility",
    "build_exercise_habit",
]
WorkoutStatus = Literal["FULL", "MINIMUM", "RECOVERY", "ZERO"]


class SafetyScreening(BaseModel):
    known_medical_restrictions: str = ""
    recent_injury: str = ""
    movement_pain: str = ""
    abnormal_symptoms: str = ""
    medical_exercise_restriction: str = ""


class OnboardingRequest(BaseModel):
    age: int = Field(ge=18, le=64)
    sex: str = Field(min_length=1, max_length=40)
    height_cm: float = Field(gt=0, le=260)
    weight_kg: float = Field(gt=0, le=500)
    training_experience: Literal["new", "beginner", "intermediate", "advanced"]
    available_training_days: int = Field(ge=1, le=7)
    session_duration_minutes: int = Field(ge=5, le=180)
    available_space: Literal["SMALL", "MEDIUM", "LARGE"]
    noise_preference: NoisePreference = "NORMAL"
    jumping_allowed: bool = True
    equipment_mode: EquipmentMode = "ZERO"
    primary_goal: Goal
    secondary_focus: str = "full_body"
    safety: SafetyScreening = Field(default_factory=SafetyScreening)


class UserResponse(OnboardingRequest):
    id: str
    created_at: str
    safety_status: Literal["SAFE", "CAUTION", "BLOCKED", "PENDING"]


class ExerciseResponse(BaseModel):
    id: str
    name: str
    name_cn: str
    movement_pattern: str
    primary_muscles: list[str]
    secondary_muscles: list[str]
    difficulty_level: int
    equipment_modes: list[EquipmentMode]
    space_requirement: str
    noise_level: str
    impact_level: str
    execution_type: str
    rep_range: dict[str, int]
    duration_range: dict[str, int]
    recommended_sets: int
    recommended_rpe: float
    recommended_rir: float
    regression_ids: list[str]
    progression_ids: list[str]
    contraindication_tags: list[str]
    restriction_tags: list[str]
    pose_supported: bool
    pose_rules: dict[str, Any]
    rom_rules: dict[str, Any]
    common_mistakes: list[str]
    coaching_cues: list[str]
    version: str
    source: str
    review_status: str


class AssessmentRequest(BaseModel):
    user_id: str
    push_up_reps: int = Field(ge=0, le=200)
    squat_reps: int = Field(ge=0, le=300)
    plank_seconds: int = Field(ge=0, le=1800)
    cardio_minutes: int = Field(ge=0, le=180)
    mobility_score: int = Field(ge=0, le=100)


class AssessmentResponse(BaseModel):
    id: str
    user_id: str
    assessed_at: str
    dimensions: dict[str, str]
    raw_inputs: dict[str, int]


class PlanRequest(BaseModel):
    user_id: str
    start_date: date | None = None
    cycle_days: int = Field(default=28, ge=7, le=56)


class WorkoutBlock(BaseModel):
    exercise_id: str
    name: str
    sets: int
    reps: int | None = None
    duration_seconds: int | None = None
    rest_seconds: int
    intent: str
    minimum: bool = False


class DailyWorkout(BaseModel):
    date: str
    day_index: int
    title: str
    focus: str
    duration_minutes: int
    kind: Literal["TRAINING", "RECOVERY"]
    blocks: list[WorkoutBlock]
    short_workout: list[WorkoutBlock] = Field(default_factory=list)
    minimum_workout: list[WorkoutBlock]


class PlanResponse(BaseModel):
    id: str
    user_id: str
    start_date: str
    end_date: str
    goal: str
    secondary_focus: str
    weekly_plan: list[DailyWorkout]


class WorkoutFeedbackRequest(BaseModel):
    user_id: str
    workout_date: date
    status: WorkoutStatus
    workout_plan: dict[str, Any]
    session_rpe: float | None = Field(default=None, ge=0, le=10)
    rir: float | None = Field(default=None, ge=0, le=5)
    soreness: int | None = Field(default=None, ge=0, le=10)
    pain: int | None = Field(default=None, ge=0, le=10)
    fatigue: int | None = Field(default=None, ge=0, le=10)
    enjoyment: int | None = Field(default=None, ge=0, le=10)
    notes: str = Field(default="", max_length=2000)


class WorkoutSessionResponse(BaseModel):
    id: str
    workout_date: str
    status: WorkoutStatus
    xp: int
    next_recommendation: str


class CoachRequest(BaseModel):
    user_id: str
    message: str = Field(min_length=1, max_length=2000)


class CoachResponse(BaseModel):
    source: Literal["ollama", "fallback"]
    fatigue: Literal["low", "moderate", "high", "unknown"]
    motivation: Literal["low", "moderate", "high", "unknown"]
    time_available_minutes: int | None = None
    recommendation: Literal["normal", "short", "minimum", "recovery", "stop"]
    reason: str
    message: str


class PoseCalibrationRequest(BaseModel):
    full_body_visibility: float = Field(ge=0, le=1)
    distance_score: float = Field(ge=0, le=1)
    angle_score: float = Field(ge=0, le=1)
    lighting_score: float = Field(ge=0, le=1)
    occlusion_score: float = Field(ge=0, le=1)
    fps: float = Field(ge=0, le=240)
    pose_confidence: float = Field(ge=0, le=1)


class LandmarkInput(BaseModel):
    x: float
    y: float
    visibility: float = Field(default=1, ge=0, le=1)


class PoseAnalyzeRequest(BaseModel):
    exercise: Literal["squat", "push_up"]
    landmarks: dict[str, LandmarkInput]
    reps_so_far: int = Field(default=0, ge=0)
    phase: Literal["UP", "DOWN"] = "UP"


class PoseAnalyzeResponse(BaseModel):
    exercise: str
    reps: int
    phase: str
    confidence: Literal["GOOD", "POTENTIAL_ISSUE", "UNABLE_TO_DETERMINE"]
    feedback: list[str]


class DashboardResponse(BaseModel):
    user: UserResponse
    current_streak: int
    longest_streak: int
    consistency: dict[str, dict[str, int | float]]
    total_training_minutes: int
    fitness_levels: dict[str, str]
    assessment_history: list[AssessmentResponse] = Field(default_factory=list)
    performance_change: dict[str, dict[str, str | int]] = Field(default_factory=dict)
    achievements: list[str] = Field(default_factory=list)
    discipline_level: str
    xp: int
    next_workout: DailyWorkout | None = None


class WellnessCheckinRequest(BaseModel):
    user_id: str
    log_date: date | None = None
    body_weight_kg: float | None = Field(default=None, gt=0, le=500)
    protein_awareness: bool | None = None
    hydration_glasses: int | None = Field(default=None, ge=0, le=40)
    fruit_vegetable_servings: int | None = Field(default=None, ge=0, le=30)
    steps: int | None = Field(default=None, ge=0, le=200000)
    daily_movement_minutes: int | None = Field(default=None, ge=0, le=1440)
    sedentary_minutes: int | None = Field(default=None, ge=0, le=1440)
    notes: str = Field(default="", max_length=2000)


class WellnessResponse(BaseModel):
    user_id: str
    log_date: str
    body_weight_kg: float | None = None
    protein_awareness: bool | None = None
    hydration_glasses: int | None = None
    fruit_vegetable_servings: int | None = None
    steps: int | None = None
    daily_movement_minutes: int | None = None
    sedentary_minutes: int | None = None
    notes: str = ""


class WellnessSummaryResponse(BaseModel):
    latest: WellnessResponse | None = None
    body_weight_trend: list[dict[str, str | float]]
    averages: dict[str, float]
