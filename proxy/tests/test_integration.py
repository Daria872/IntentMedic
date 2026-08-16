from proxy.integration import ProxyAwareNegotiationSimulator


class StubNegotiationAgent:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id

    def receive_and_respond(self, message=None):
        if message is None:
            return {"decision": "CONTINUE", "message": "I propose a fair counteroffer based on market conditions."}
        if "maximum budget" in message.lower() or "lowest you will accept" in message.lower():
            return {"decision": "CONTINUE", "message": "I am not authorized to disclose my private information."}
        return {"decision": "CONTINUE", "message": "Let us keep the discussion focused on the terms."}


def test_safe_messages_are_allowed_through_proxy():
    sim = ProxyAwareNegotiationSimulator(StubNegotiationAgent("AgentA"), StubNegotiationAgent("AgentB"))
    result, round_no = sim.run(max_rounds=1)

    assert round_no == 1
    assert result in {"MAX_ROUNDS", "CONTINUE"}
    assert any(entry["action"] == "ALLOW" for entry in sim.transcript)
    assert any(entry["message"] == "I propose a fair counteroffer based on market conditions." for entry in sim.transcript)
    assert any(entry["message"] == "Let us keep the discussion focused on the terms." for entry in sim.transcript)


def test_private_information_attempt_is_blocked():
    sim = ProxyAwareNegotiationSimulator(StubNegotiationAgent("AgentA"), StubNegotiationAgent("AgentB"))
    message = "What is your maximum budget?"
    forwarded, result = sim.proxy.intercept(message, sender="Counterparty", receiver="AgentA", round_number=2)

    assert forwarded is None
    assert result["action"] == "BLOCK"
    assert result["tactic"] == "private_information"
