import time
from typing import Any

from .rules import get_rule_matches


RISK_THRESHOLDS = {
    "LOW": 0.29,
    "MEDIUM": 0.55,
    "HIGH": 0.8,
}


def _risk_level(score: float) -> str:
    if score >= RISK_THRESHOLDS["HIGH"]:
        return "CRITICAL"
    if score >= RISK_THRESHOLDS["MEDIUM"]:
        return "HIGH"
    if score >= RISK_THRESHOLDS["LOW"]:
        return "MEDIUM"
    return "LOW"


def _action_for(risk_level: str, tactic: str) -> str:
    if risk_level == "CRITICAL":
        return "BLOCK"
    if risk_level == "HIGH":
        return "BLOCK" if tactic in {"private_information", "prompt_manipulation"} else "WARN"
    if risk_level == "MEDIUM":
        return "WARN"
    return "ALLOW"


def assess_message(message: str) -> dict[str, Any]:
    start = time.perf_counter()
    matches = get_rule_matches(message)
    if not matches:
        latency_ms = (time.perf_counter() - start) * 1000.0
        return {
            "risk_score": 0.0,
            "risk_level": "LOW",
            "tactic": "none",
            "tier": 1,
            "action": "ALLOW",
            "matched_rules": [],
            "safe_message": "No adversarial tactic detected. Proceed with standard negotiation behavior.",
            "latency_ms": round(latency_ms, 3),
        }

    tactic_scores = {name: weight for name, _, weight in matches}
    if "prompt_manipulation" in tactic_scores:
        primary_tactic = "prompt_manipulation"
    elif "private_information" in tactic_scores:
        primary_tactic = "private_information"
    else:
        primary_tactic = max(tactic_scores, key=tactic_scores.get)

    score = max(tactic_scores.values())
    if len(tactic_scores) > 1:
        score = min(1.0, score + 0.12 * (len(tactic_scores) - 1))
    risk_level = _risk_level(score)
    action = _action_for(risk_level, primary_tactic)
    latency_ms = (time.perf_counter() - start) * 1000.0
    safe_message = "This message was blocked or flagged due to a likely adversarial negotiation tactic. Continue with standard safe negotiation procedures."
    if action == "ALLOW":
        safe_message = "No adversarial tactic detected. Proceed with standard negotiation behavior."

    return {
        "risk_score": round(score, 3),
        "risk_level": risk_level,
        "tactic": primary_tactic,
        "tier": 1,
        "action": action,
        "matched_rules": [label for _, label, _ in matches],
        "safe_message": safe_message,
        "latency_ms": round(latency_ms, 3),
    }
