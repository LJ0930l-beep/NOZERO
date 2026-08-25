"""Schema validation boundary for local-model responses."""

from __future__ import annotations

from typing import Any

from ai.schemas.coach import CoachDecision


class ResponseParser:
    """Turn untrusted model payloads into validated domain responses."""

    @staticmethod
    def coach(payload: dict[str, Any]) -> CoachDecision:
        return CoachDecision.model_validate(payload)
