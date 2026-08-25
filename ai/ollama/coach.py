"""Fitness coach facade over Ollama and the response parser."""

from __future__ import annotations

from ai.ollama.client import OllamaClient
from ai.ollama.parser import ResponseParser
from ai.ollama.router import PromptRouter
from ai.schemas.coach import CoachDecision


class FitnessCoach:
    """The model can explain a deterministic plan but cannot change it."""

    def __init__(
        self,
        client: OllamaClient,
        prompt_router: PromptRouter | None = None,
        response_parser: ResponseParser | None = None,
    ) -> None:
        self.client = client
        self.prompt_router = prompt_router or PromptRouter()
        self.response_parser = response_parser or ResponseParser()

    def generate(self, message: str, context: str) -> CoachDecision:
        prompt = self.prompt_router.coach(message, context)
        return self.response_parser.coach(self.client.generate_json(prompt))
