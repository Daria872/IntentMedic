import re
from typing import Iterable


RULE_DEFINITIONS = {
    "reservation_value": {
        "weight": 0.72,
        "patterns": [
            r"lowest\s+(?:you\s+)?will\s+accept",
            r"minimum\s+(?:you\s+)?will\s+accept",
            r"least\s+(?:you\s+)?will\s+accept",
            r"reservation\s+value",
        ],
        "label": "reservation_value:lowest_you_will_accept",
    },
    "batna": {
        "weight": 0.68,
        "patterns": [
            r"fallback",
            r"best\s+alternative",
            r"batna",
            r"alternative\s+to\s+negotiation",
        ],
        "label": "batna:fallback_or_alternative",
    },
    "private_information": {
        "weight": 0.94,
        "patterns": [
            r"maximum\s+budget",
            r"max\s+budget",
            r"highest\s+budget",
            r"private\s+priorit",
            r"private\s+state",
        ],
        "label": "private_information:max_budget_or_private_state",
    },
    "pressure_urgency": {
        "weight": 0.52,
        "patterns": [
            r"decide\s+now",
            r"act\s+now",
            r"urgent",
            r"immediately",
            r"without\s+delay",
            r"this\s+is\s+time-sensitive",
        ],
        "label": "pressure_urgency:urgent_decision",
    },
    "anchoring": {
        "weight": 0.58,
        "patterns": [
            r"everyone\s+pays\s+\$?\d+(?:[.,]\d+)?",
            r"everyone\s+pays\s+[a-zA-Z]*\s*\d+(?:[.,]\d+)?",
            r"anchor(?:ing)?",
            r"standard\s+rate\s+is",
        ],
        "label": "anchoring:everyone_pays",
    },
    "prompt_manipulation": {
        "weight": 0.90,
        "patterns": [
            r"ignore\s+your\s+instructions",
            r"ignore\s+the\s+instructions",
            r"reveal\s+your\s+private\s+state",
            r"override\s+your\s+constraints",
            r"disregard\s+your\s+instructions",
            r"bypass\s+your\s+policy",
        ],
        "label": "prompt_manipulation:instruction_override",
    },
}


def _normalize_message(message: str) -> str:
    return re.sub(r"\s+", " ", message or "").strip().lower()


def get_rule_matches(message: str) -> list[tuple[str, str, float]]:
    normalized = _normalize_message(message)
    matches: list[tuple[str, str, float]] = []
    for tactic, config in RULE_DEFINITIONS.items():
        for pattern in config["patterns"]:
            if re.search(pattern, normalized, flags=re.IGNORECASE):
                matches.append((tactic, config["label"], float(config["weight"])))
                break
    return matches


def fake_keyword_scan(message: str) -> Iterable[str]:
    """Compatibility helper for future Tier 2/Tier 3 expansion."""
    return [label for _, label, _ in get_rule_matches(message)]
