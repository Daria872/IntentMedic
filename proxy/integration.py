import time
from dataclasses import dataclass, field
from typing import Any, Optional

from fastapi.testclient import TestClient

from .main import app


@dataclass
class ProxyLogEntry:
    round: int
    sender: str
    receiver: str
    message: str
    tier_1_result: dict[str, Any]
    action: str
    latency: float


class Tier1ProxyBridge:
    """Adapter that enforces the Tier 1 /intercept route for all message traffic."""

    def __init__(self, client: Optional[TestClient] = None):
        self.client = client or TestClient(app)
        self.logs: list[ProxyLogEntry] = []

    def intercept(self, message: str, sender: str, receiver: str, round_number: int) -> tuple[Optional[str], dict[str, Any]]:
        if not message:
            return message, {"risk_level": "LOW", "action": "ALLOW", "risk_score": 0.0, "tactic": "none", "tier": 1, "matched_rules": [], "safe_message": "No message to inspect.", "latency_ms": 0.0}

        start = time.perf_counter()
        response = self.client.post("/intercept", json={"message": message})
        result = response.json()
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        result["latency_ms"] = round(float(result.get("latency_ms", elapsed_ms)), 3)

        log_entry = ProxyLogEntry(
            round=round_number,
            sender=sender,
            receiver=receiver,
            message=message,
            tier_1_result={
                "risk_score": result.get("risk_score"),
                "risk_level": result.get("risk_level"),
                "tactic": result.get("tactic"),
                "tier": result.get("tier"),
                "action": result.get("action"),
                "matched_rules": result.get("matched_rules", []),
                "safe_message": result.get("safe_message"),
                "latency_ms": result.get("latency_ms", 0.0),
            },
            action=result.get("action", "ALLOW"),
            latency=round(float(result.get("latency_ms", elapsed_ms)), 3),
        )
        self.logs.append(log_entry)

        if result.get("action") == "BLOCK":
            return None, result
        return message, result


class ProxyAwareNegotiationSimulator:
    """Minimal integration layer around the existing negotiation agent flow."""

    def __init__(self, agent_a, agent_b, proxy_bridge: Optional[Tier1ProxyBridge] = None):
        self.agent_a = agent_a
        self.agent_b = agent_b
        self.proxy = proxy_bridge or Tier1ProxyBridge()
        self.transcript: list[dict[str, Any]] = []

    def _log_transcript(self, round_number: int, sender: str, receiver: str, message: str, result: dict[str, Any], action: str, latency_ms: float):
        self.transcript.append(
            {
                "round": round_number,
                "sender": sender,
                "receiver": receiver,
                "message": message,
                "tier_1_result": {
                    "risk_score": result.get("risk_score"),
                    "risk_level": result.get("risk_level"),
                    "tactic": result.get("tactic"),
                    "tier": result.get("tier"),
                    "action": action,
                    "matched_rules": result.get("matched_rules", []),
                    "safe_message": result.get("safe_message"),
                    "latency_ms": latency_ms,
                },
                "action": action,
                "latency": latency_ms,
            }
        )

    def run(self, max_rounds: int = 5):
        last_message: Optional[str] = None

        for round_number in range(1, max_rounds + 1):
            if last_message is not None:
                checked_message, result = self.proxy.intercept(
                    message=last_message,
                    sender=self.agent_b.agent_id,
                    receiver=self.agent_a.agent_id,
                    round_number=round_number,
                )
                if checked_message is None:
                    self._log_transcript(round_number, self.agent_b.agent_id, self.agent_a.agent_id, last_message, result, result.get("action", "BLOCK"), result.get("latency_ms", 0.0))
                    return "BLOCKED", round_number
                last_message = checked_message
            else:
                last_message = None

            response_a = self.agent_a.receive_and_respond(last_message)
            self.transcript.append({
                "round": round_number,
                "sender": self.agent_a.agent_id,
                "receiver": self.agent_b.agent_id,
                "message": response_a["message"],
                "tier_1_result": {"action": "ALLOW"},
                "action": "ALLOW",
                "latency": 0.0,
            })

            forwarded_a, result_a = self.proxy.intercept(
                message=response_a["message"],
                sender=self.agent_a.agent_id,
                receiver=self.agent_b.agent_id,
                round_number=round_number,
            )
            self._log_transcript(round_number, self.agent_a.agent_id, self.agent_b.agent_id, response_a["message"], result_a, result_a.get("action", "ALLOW"), result_a.get("latency_ms", 0.0))

            if forwarded_a is None:
                return "BLOCKED", round_number

            response_b = self.agent_b.receive_and_respond(forwarded_a)
            self.transcript.append({
                "round": round_number,
                "sender": self.agent_b.agent_id,
                "receiver": self.agent_a.agent_id,
                "message": response_b["message"],
                "tier_1_result": {"action": "ALLOW"},
                "action": "ALLOW",
                "latency": 0.0,
            })

            if response_b["decision"] in ["ACCEPT", "WALK_AWAY"]:
                return response_b["decision"], round_number

            last_message = response_b["message"]

            next_message, result_b = self.proxy.intercept(
                message=last_message,
                sender=self.agent_b.agent_id,
                receiver=self.agent_a.agent_id,
                round_number=round_number,
            )
            self._log_transcript(round_number, self.agent_b.agent_id, self.agent_a.agent_id, last_message, result_b, result_b.get("action", "ALLOW"), result_b.get("latency_ms", 0.0))

            if next_message is None:
                return "BLOCKED", round_number

            last_message = next_message

        return "MAX_ROUNDS", max_rounds
