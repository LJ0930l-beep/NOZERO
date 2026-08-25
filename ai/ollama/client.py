"""Minimal dependency-free Ollama HTTP client with JSON validation boundary."""

from __future__ import annotations

import json
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class OllamaUnavailable(RuntimeError):
    """Raised when the local model service cannot be reached."""


class OllamaClient:
    def __init__(self, base_url: str, model: str, timeout_seconds: float = 20) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def generate_json(self, prompt: str) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.2},
        }
        request = Request(
            f"{self.base_url}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise OllamaUnavailable(str(exc)) from exc
        raw = body.get("response", body)
        if isinstance(raw, dict):
            return raw
        if not isinstance(raw, str):
            raise OllamaUnavailable("Ollama returned a non-JSON response")
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
            if not match:
                raise OllamaUnavailable("Ollama response did not contain JSON")
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError as exc:
                raise OllamaUnavailable("Ollama response JSON was invalid") from exc
