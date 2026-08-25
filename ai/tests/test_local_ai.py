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
