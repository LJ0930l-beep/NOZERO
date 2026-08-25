import pytest

from ai.ollama.review import WeeklyReview
from ai.ollama.service import LocalAIService


class FakeClient:
    def __init__(self, payload):
        self.payload = payload

    def generate_json(self, prompt: str):
        return self.payload


def test_local_ai_validates_structured_output() -> None:
    service = LocalAIService(
        FakeClient(
            {
                "fatigue": "moderate",
                "motivation": "high",
                "recommendation": "short",
                "reason": "limited time",
                "message": "short session",
            }
        )
    )
    source, decision = service.coach("I have 12 minutes", {"safety_status": "SAFE"}, {}, [], "NORMAL", {}, "SAFE")
    assert source == "ollama"
    assert decision.recommendation == "short"


def test_local_ai_fallback_stops_on_safety_block() -> None:
    service = LocalAIService(FakeClient({}), allow_model=True)
    source, decision = service.coach("I want to train", {"safety_status": "BLOCKED"}, {}, [], "NORMAL", {}, "BLOCKED")
    assert source == "fallback"
    assert decision.recommendation == "stop"


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("今天累死了", "minimum"),
        ("我只有5分钟", "minimum"),
        ("腿很痛但我想继续练腿", "recovery"),
        ("给我安排300个深蹲", "short"),
        ("我要每天练胸", "short"),
        ("我胸痛但想坚持训练", "stop"),
    ],
)
def test_local_ai_fallback_covers_explicit_safety_and_dose_prompts(message: str, expected: str) -> None:
    service = LocalAIService(FakeClient({}), allow_model=False)
    _, decision = service.coach(message, {"safety_status": "SAFE"}, {}, [], "NORMAL", {}, "SAFE")
    assert decision.recommendation == expected


def test_model_cannot_override_a_more_conservative_fallback() -> None:
    service = LocalAIService(
        FakeClient(
            {
                "fatigue": "low",
                "motivation": "high",
                "recommendation": "normal",
                "reason": "model suggestion",
                "message": "normal session",
            }
        )
    )
    source, decision = service.coach("今天累死了", {"safety_status": "SAFE"}, {}, [], "NORMAL", {}, "SAFE")
    assert source == "fallback"
    assert decision.recommendation == "minimum"


def test_weekly_review_uses_only_structured_session_facts() -> None:
    metrics = WeeklyReview.summarize(
        [
            {"status": "FULL", "workout_plan": {"duration_minutes": 20}},
            {"status": "RECOVERY", "workout_plan": {"duration_minutes": 10}},
            {"status": "ZERO", "workout_plan": {"duration_minutes": 0}},
        ]
    )
    assert metrics["sessions_completed"] == 2
    assert metrics["training_time_minutes"] == 30
    assert metrics["zero_days"] == 1
