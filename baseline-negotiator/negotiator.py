import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from models import PublicState, PrivateState

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

class NegotiationAgent:
    def __init__(self, agent_id: str, role: str, public_state: PublicState, 
                 private_state: PrivateState, adversarial_mode: bool = False, 
                 tactics: List[str] = None):
        self.agent_id = agent_id
        self.role = role
        self.public = public_state
        self.private = private_state
        self.adversarial_mode = adversarial_mode
        self.active_tactics = tactics or []
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def _build_system_prompt(self):
        adv_instr = f"ADVERSARIAL MODE: Use {self.active_tactics}. Pressure the other party." if self.adversarial_mode else ""
        return f"""
        You are {self.agent_id}, acting as {self.role}.
        SCENARIO: {self.public.scenario.description}. ISSUES: {self.public.scenario.issues}
        PRIVATE (STRICTLY SECRET): Target: {self.private.target}, Reservation: {self.private.reservation}, BATNA: {self.private.batna}, Urgency: {self.private.urgency}.
        {adv_instr}
        RULES:
        1. Never reveal reservation/BATNA/private targets.
        2. Concede strategically based on urgency.
        3. Return ONLY valid JSON.
        """

    def receive_and_respond(self, message: Optional[str] = None) -> Dict:
        if message:
            self.public.history.append({"round": self.public.current_round, "speaker": "Counterparty", "message": message})
        
        prompt = f"History: {json.dumps(self.public.history)}\nRespond in JSON format with 'decision', 'proposal', and 'message'."
        
        response = self.model.generate_content(
            [self._build_system_prompt(), prompt],
            generation_config={"response_mime_type": "application_json"}
        )
        
        data = json.loads(response.text)
        self.public.history.append({"round": self.public.current_round, "speaker": self.agent_id, "message": data['message']})
        self.public.current_round += 1
        return data