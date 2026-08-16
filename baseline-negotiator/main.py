from models import NegotiationScenario, PublicState, PrivateState
from negotiator import NegotiationAgent
from simulator import NegotiationSimulator

def test():
    scen = NegotiationScenario("Partnership", "Software Licensing", ["price", "duration"])
    a_priv = PrivateState({"price": 1000}, {"price": 1500}, "Internal Build", 0.5, {"price": 10})
    b_priv = PrivateState({"price": 2000}, {"price": 1200}, "Other Vendor", 0.8, {"price": 10})
    
    agent = NegotiationAgent("AgentA", "Buyer", PublicState(scen), a_priv)
    cp = NegotiationAgent("AgentB", "Seller", PublicState(scen), b_priv, adversarial_mode=True, tactics=["anchoring"])
    
    sim = NegotiationSimulator(agent, cp)
    result, rounds = sim.run()
    
    for entry in sim.transcript:
        print(f"Round {entry['round']} | {entry['speaker']}: {entry['message']}")
    print(f"Result: {result}")

if __name__ == "__main__":
    test()