from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class NegotiationScenario:
    name: str
    description: str
    issues: List[str]

@dataclass
class PublicState:
    scenario: NegotiationScenario
    history: List[Dict] = field(default_factory=list)
    current_round: int = 1
    status: str = "IN_PROGRESS"

@dataclass
class PrivateState:
    target: Dict[str, any]
    reservation: Dict[str, any]
    batna: str
    urgency: float  
    priorities: Dict[str, int]