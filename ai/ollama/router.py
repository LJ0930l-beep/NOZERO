"""Prompt routing for the local AI boundary."""

from __future__ import annotations


class PromptRouter:
    """Builds bounded prompts without allowing the model to own domain rules."""

    def coach(self, message: str, context: str) -> str:
        return (
            "You are a conservative local fitness coach. Return only JSON matching this schema: "
            '{"fatigue":"low|moderate|high|unknown","motivation":"low|moderate|high|unknown",'
            '"time_available_minutes":number|null,"recommendation":"normal|short|minimum|recovery|stop",'
            '"reason":"string","message":"string"}. '
            "Never diagnose. Never override safety, recovery, or exercise restrictions. "
            f"USER_MESSAGE={message}\nSTRUCTURED_CONTEXT={context}"
        )
