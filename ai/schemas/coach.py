"""Structured output contract for local coach calls."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class CoachDecision(BaseModel):
    fatigue: Literal["low", "moderate", "high", "unknown"] = "unknown"
    motivation: Literal["low", "moderate", "high", "unknown"] = "unknown"
    time_available_minutes: int | None = Field(default=None, ge=0, le=240)
    recommendation: Literal["normal", "short", "minimum", "recovery", "stop"] = "normal"
    reason: str = Field(min_length=1, max_length=1000)
    message: str = Field(min_length=1, max_length=2000)
