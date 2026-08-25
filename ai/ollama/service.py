"""Local Qwen coach with deterministic safety-aware fallback."""

from __future__ import annotations

import re
from typing import Any

from ai.ollama.client import OllamaClient, OllamaUnavailable
from ai.ollama.context import build_context
from ai.schemas.coach import CoachDecision


class LocalAIService:
    """All Ollama calls go through this boundary; routes never call Ollama directly."""

    def __init__(self, client: OllamaClient, allow_model: bool = True) -> None:
        self.client = client
        self.allow_model = allow_model

    def coach(
        self,
        message: str,
        user: dict[str, Any],
        today_plan: dict[str, Any] | None,
        recent_sessions: list[dict[str, Any]],
        recovery_status: str,
        memories: dict[str, str],
        safety_status: str,
    ) -> tuple[str, CoachDecision]:
        fallback = self._fallback(message, user, recovery_status, safety_status)
        if not self.allow_model or safety_status == "BLOCKED":
            return "fallback", fallback
        context = build_context(user, today_plan, recent_sessions, recovery_status, memories)
        prompt = (
            "You are a conservative local fitness coach. Return only JSON matching this schema: "
            '{"fatigue":"low|moderate|high|unknown","motivation":"low|moderate|high|unknown",'
            '"time_available_minutes":number|null,"recommendation":"normal|short|minimum|recovery|stop",'
            '"reason":"string","message":"string"}. '
            "Never diagnose. Never override safety, recovery, or exercise restrictions. "
            f"USER_MESSAGE={message}\nSTRUCTURED_CONTEXT={context}"
        )
        try:
            decision = CoachDecision.model_validate(self.client.generate_json(prompt))
            if safety_status == "BLOCKED" and decision.recommendation != "stop":
                return "fallback", fallback
            return "ollama", decision
        except (OllamaUnavailable, ValueError, TypeError):
            return "fallback", fallback

    @staticmethod
    def _fallback(message: str, user: dict[str, Any], recovery_status: str, safety_status: str) -> CoachDecision:
        text = message.lower()
        if safety_status == "BLOCKED":
            return CoachDecision(
                fatigue="unknown",
                motivation="unknown",
                recommendation="stop",
                reason="safety screening found a red-flag symptom or restriction",
                message="先停止正常训练流程；如果症状明显或持续，请寻求合适的专业医疗意见。",
            )
        if recovery_status == "RECOVERY" or any(
            term in text for term in ("胸痛", "晕厥", "严重呼吸", "chest pain", "faint")
        ):
            return CoachDecision(
                fatigue="high",
                motivation="unknown",
                recommendation="stop",
                reason="pain or a red-flag symptom needs safety review before exercise",
                message="当前不适合继续训练，先停止并进行安全评估。",
            )
        time_match = re.search(r"(\d{1,3})\s*(?:分钟|min|minutes?)", text)
        minutes = int(time_match.group(1)) if time_match else None
        high_fatigue = any(term in text for term in ("累死", "很累", "疲劳", "exhausted", "tired"))
        low_motivation = any(term in text for term in ("不想", "没动力", "懒", "low motivation"))
        if high_fatigue or (minutes is not None and minutes <= 6) or low_motivation:
            recommendation = "minimum" if minutes is None or minutes <= 8 else "short"
            reason = "high fatigue, low motivation, or limited time favors a plan-derived minimum dose"
            message_text = "今天做原计划的最小版本，保留动作逻辑，降低训练量即可。"
            return CoachDecision(
                fatigue="high" if high_fatigue else "moderate",
                motivation="low" if low_motivation else "moderate",
                time_available_minutes=minutes,
                recommendation=recommendation,
                reason=reason,
                message=message_text,
            )
        return CoachDecision(
            fatigue="low",
            motivation="moderate",
            time_available_minutes=minutes,
            recommendation="normal",
            reason="no high-risk or high-fatigue signal was found",
            message="按今天的计划开始；如果动作质量下降，就降低难度或切换到最小版本。",
        )
