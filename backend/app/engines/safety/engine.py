"""Safety-first screening; this module is never delegated to the LLM."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SafetyResult:
    status: str
    blockers: list[str]
    cautions: list[str]
    recommended_action: str
    blocked_tags: list[str] = field(default_factory=list)
    caution_tags: list[str] = field(default_factory=list)


RED_FLAGS = {
    "chest pain": "chest pain",
    "胸痛": "胸痛",
    "fainting": "fainting",
    "fainted": "fainting",
    "晕厥": "晕厥",
    "severe breathing": "severe breathing difficulty",
    "呼吸困难": "breathing difficulty",
    "急性伤": "acute injury",
    "acute injury": "acute injury",
    "严重不适": "serious exercise-related discomfort",
}
CAUTION_TERMS = {
    "injury": "recent injury",
    "受伤": "recent injury",
    "pain": "movement pain",
    "疼": "movement pain",
    "medical restriction": "medical exercise restriction",
    "医生": "medical advice or restriction",
    "限制": "medical exercise restriction",
}
NEGATIONS = ("no ", "none", "without", "没有", "无", "否认", "否")
EMPTY_VALUES = {"", "n/a", "na", "nil", "none", "no", "无", "没有", "否", "否认"}


def _active_terms(value: Any, terms: dict[str, str]) -> list[str]:
    if isinstance(value, bool):
        return []
    text = str(value or "").strip().lower()
    if text in EMPTY_VALUES:
        return []
    found: list[str] = []
    for phrase, label in terms.items():
        start = text.find(phrase)
        if start < 0:
            continue
        prefix = text[max(0, start - 12) : start]
        if any(negation in prefix for negation in NEGATIONS):
            continue
        if label not in found:
            found.append(label)
    return found


def screen_safety(screening: dict[str, Any]) -> SafetyResult:
    blockers: list[str] = []
    cautions: list[str] = []
    structured_red_flags = {
        "exercise_chest_pain": "chest pain",
        "fainting_or_dizziness": "fainting or dizziness",
        "unusual_shortness_of_breath": "unusual shortness of breath",
    }
    for field_name, label in structured_red_flags.items():
        if screening.get(field_name) is True:
            blockers.append(label)
    for field_name, value in screening.items():
        if value is None or value is False:
            continue
        blockers.extend(_active_terms(value, RED_FLAGS))
        cautions.extend(_active_terms(value, CAUTION_TERMS))
        if field_name == "known_medical_restrictions" and str(value).strip().lower() not in EMPTY_VALUES:
            cautions.append("known medical restriction")
        if field_name == "medical_exercise_restriction" and str(value).strip().lower() not in EMPTY_VALUES:
            cautions.append("medical exercise restriction")
    blockers = sorted(set(blockers))
    cautions = sorted(set(cautions) - set(blockers))
    from backend.app.engines.safety.restrictions import resolve_restrictions

    restriction = resolve_restrictions(screening)
    if blockers:
        return SafetyResult(
            "BLOCKED",
            blockers,
            cautions,
            "stop normal training and seek professional medical advice",
            restriction.blocked_tags,
            restriction.caution_tags,
        )
    if cautions:
        return SafetyResult(
            "CAUTION",
            [],
            cautions,
            "use conservative options and obtain professional guidance where appropriate",
            restriction.blocked_tags,
            restriction.caution_tags,
        )
    return SafetyResult(
        "SAFE",
        [],
        [],
        "continue with the planned safety-validated session",
        restriction.blocked_tags,
        restriction.caution_tags,
    )
