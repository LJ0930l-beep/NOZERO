"""Local Qwen coach with deterministic safety-aware fallback."""

from __future__ import annotations

import re
from typing import Any

from ai.ollama.client import OllamaClient, OllamaUnavailable
from ai.ollama.coach import FitnessCoach
from ai.ollama.context import ContextBuilder
from ai.schemas.coach import CoachDecision


class LocalAIService:
    """All Ollama calls go through this boundary; routes never call Ollama directly."""

    def __init__(self, client: OllamaClient, allow_model: bool = True) -> None:
        self.client = client
        self.allow_model = allow_model
        self.fitness_coach = FitnessCoach(client)

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
        context = ContextBuilder.build(user, today_plan, recent_sessions, recovery_status, memories)
        try:
            decision = self.fitness_coach.generate(message, context)
            priority = {"normal": 0, "short": 1, "minimum": 2, "recovery": 3, "stop": 4}
            if priority[decision.recommendation] < priority[fallback.recommendation]:
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
        if safety_status == "CAUTION":
            return CoachDecision(
                fatigue="unknown",
                motivation="moderate",
                recommendation="short",
                reason="a screening caution requires a conservative reduced session",
                message="当前有安全注意事项，先采用短版、无痛范围和低冲击选项；如有疑问请先获得专业意见。",
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
        if any(term in text for term in ("腿很痛", "很痛", "疼", "受伤", "pain", "injury")):
            return CoachDecision(
                fatigue="moderate",
                motivation="unknown",
                recommendation="recovery",
                reason="reported pain or injury language requires a recovery-focused downgrade",
                message="先不要继续刺激疼痛部位，切换到恢复或寻求合适的专业意见。",
            )
        if any(
            term in text
            for term in (
                "300个", "300次", "每天练胸", "每天练腿", "every day", "daily chest", "无限增加", "more volume"
            )
        ):
            return CoachDecision(
                fatigue="unknown",
                motivation="high",
                time_available_minutes=None,
                recommendation="short",
                reason="arbitrary high volume or daily single-pattern training is not a safe progression rule",
                message="不安排任意堆量；按今天计划的剂量执行，下一次进阶需要真实完成度、RPE/RIR 和动作质量。",
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
