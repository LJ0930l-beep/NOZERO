"""Safety-first screening; this module is never delegated to the LLM."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SafetyResult:
    status: str
    blockers: list[str]
    cautions: list[str]
    recommended_action: str


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


def _active_terms(value: str, terms: dict[str, str]) -> list[str]:
    text = value.strip().lower()
    if not text or text in {"n/a", "na", "nil", "none", "无"}:
        return []
    found: list[str] = []
    for phrase, label in terms.items():
        start = text.find(phrase)
        if start < 0:
            continue
        prefix = text[max(0, start - 8) : start]
        if any(negation in prefix for negation in NEGATIONS):
            continue
        if label not in found:
            found.append(label)
    return found


def screen_safety(screening: dict[str, str]) -> SafetyResult:
    blockers: list[str] = []
    cautions: list[str] = []
    for field_name, value in screening.items():
        if not value:
            continue
        blockers.extend(_active_terms(value, RED_FLAGS))
        cautions.extend(_active_terms(value, CAUTION_TERMS))
        if field_name == "known_medical_restrictions" and value.strip():
            cautions.append("known medical restriction")
        if field_name == "medical_exercise_restriction" and value.strip():
            cautions.append("medical exercise restriction")
    blockers = sorted(set(blockers))
    cautions = sorted(set(cautions) - set(blockers))
    if blockers:
        return SafetyResult("BLOCKED", blockers, cautions, "stop normal training and seek professional medical advice")
    if cautions:
        return SafetyResult(
            "CAUTION", [], cautions, "use conservative options and obtain professional guidance where appropriate"
        )
    return SafetyResult("SAFE", [], [], "continue with the planned safety-validated session")
