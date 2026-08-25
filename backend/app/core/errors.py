"""Domain errors translated to stable API responses."""

from __future__ import annotations


class NozeeroError(Exception):
    """Base class for expected domain failures."""


class SafetyBlockedError(NozeeroError):
    """Raised when a red-flag safety result blocks normal training."""

    def __init__(self, message: str, blockers: list[str] | None = None) -> None:
        super().__init__(message)
        self.blockers = blockers or []


class ResourceNotFoundError(NozeeroError):
    """Raised when an expected user, plan, or exercise is absent."""
