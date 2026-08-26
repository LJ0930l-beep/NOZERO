"""Normalize safety answers into deterministic exercise restrictions."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RestrictionResolution:
    blocked_tags: list[str] = field(default_factory=list)
    caution_tags: list[str] = field(default_factory=list)
    reasons: dict[str, list[str]] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "blocked_tags": list(self.blocked_tags),
            "caution_tags": list(self.caution_tags),
            "reasons": {key: list(value) for key, value in self.reasons.items()},
        }


EMPTY_VALUES = {"", "none", "no", "n/a", "na", "nil", "无", "没有", "否", "否认"}
ANATOMY_TAGS = (
    (("knee", "knees", "膝"), "acute_knee_pain", "knee-sensitive movement"),
    (("wrist", "wrists", "腕"), "acute_wrist_pain", "wrist-sensitive movement"),
    (("shoulder", "shoulders", "肩"), "acute_shoulder_pain", "shoulder-sensitive movement"),
    (("low back", "lower back", "腰", "下背", "背部"), "acute_low_back_pain", "low-back-sensitive movement"),
    (("hip", "hips", "髋"), "acute_hip_pain", "hip-sensitive movement"),
    (("neck", "颈"), "neck_pain", "neck-sensitive movement"),
    (("balance", "平衡"), "balance_limit", "balance-demanding movement"),
)

SENSITIVE_PATTERNS = {
    "acute_wrist_pain": {"Horizontal Push", "Vertical Push"},
}


def _active_text(value: Any) -> str:
    if isinstance(value, bool):
        return "active" if value else ""
    text = str(value or "").strip().lower()
    return "" if text in EMPTY_VALUES else text


def resolve_restrictions(screening: dict[str, Any]) -> RestrictionResolution:
    """Resolve recent injury, pain, and medical restrictions before filtering."""

    source_fields = ("recent_injury", "movement_pain", "known_medical_restrictions", "medical_exercise_restriction")
    text = " ".join(value for field in source_fields if (value := _active_text(screening.get(field))))
    blocked: set[str] = set()
    caution: set[str] = set()
    reasons: dict[str, list[str]] = {}
    for keywords, tag, reason in ANATOMY_TAGS:
        matches = [text.find(keyword) for keyword in keywords if text.find(keyword) >= 0]
        negated = any(
            text[max(0, position - 10) : position].strip().endswith(("no", "没有", "无", "否"))
            for position in matches
        )
        if matches and not negated:
            blocked.add(tag)
            reasons.setdefault(tag, []).append(reason)
    if _active_text(screening.get("recent_injury")):
        caution.add("recent_injury")
        reasons.setdefault("recent_injury", []).append("recent injury requires a conservative variation")
    if _active_text(screening.get("movement_pain")):
        caution.add("movement_pain")
        reasons.setdefault("movement_pain", []).append("keep range and impact pain-free")
    if _active_text(screening.get("known_medical_restrictions")) or _active_text(
        screening.get("medical_exercise_restriction")
    ):
        caution.add("medical_restriction")
        reasons.setdefault("medical_restriction", []).append("follow the stated medical restriction")
    return RestrictionResolution(sorted(blocked), sorted(caution), reasons)


def filter_exercises(
    exercises: Iterable[dict[str, Any]], resolution: RestrictionResolution
) -> list[dict[str, Any]]:
    """Exclude contraindicated movements and annotate conservative alternatives."""

    result: list[dict[str, Any]] = []
    blocked_tags = set(resolution.blocked_tags)
    caution_tags = set(resolution.caution_tags)
    for exercise in exercises:
        contraindications = set(exercise.get("contraindication_tags", []))
        blocked = sorted(contraindications & blocked_tags)
        pattern = str(exercise.get("movement_pattern", ""))
        blocked.extend(
            tag
            for tag, patterns in SENSITIVE_PATTERNS.items()
            if tag in blocked_tags and pattern in patterns and tag not in blocked
        )
        if blocked:
            continue
        item = dict(exercise)
        restriction_tags = set(exercise.get("restriction_tags", []))
        has_caution = bool(caution_tags and restriction_tags)
        item["selection_status"] = "CAUTION" if has_caution else "SAFE"
        item["selection_reasons"] = []
        if has_caution:
            for tag in sorted(caution_tags):
                item["selection_reasons"].extend(resolution.reasons.get(tag, []))
            if not item["selection_reasons"]:
                item["selection_reasons"] = ["use the exercise restriction tag conservatively"]
        result.append(item)
    return result
