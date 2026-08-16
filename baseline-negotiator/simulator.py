class NegotiationSimulator:
    def __init__(self, agent_a, agent_b):
        self.agent_a = agent_a
        self.agent_b = agent_b
        self.transcript = []

    def run(self, max_rounds=5):
        last_msg = None
        for r in range(1, max_rounds + 1):
            res_a = self.agent_a.receive_and_respond(last_msg)
            self.transcript.append({"round": r, "speaker": self.agent_a.agent_id, "message": res_a['message']})
            if res_a['decision'] in ['ACCEPT', 'WALK_AWAY']: return res_a['decision'], r
            
            res_b = self.agent_b.receive_and_respond(res_a['message'])
            self.transcript.append({"round": r, "speaker": self.agent_b.agent_id, "message": res_b['message']})
            if res_b['decision'] in ['ACCEPT', 'WALK_AWAY']: return res_b['decision'], r
            last_msg = res_b['message']
        return "MAX_ROUNDS", max_rounds