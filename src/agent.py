import json
from typing import Dict, Any
from src.models import AgentProfile, MarketEvent, LLMDecision

class AgentBrain:
    def __init__(self, profile: AgentProfile, api_key: str):
        self.profile = profile
        self.api_key = api_key

    async def _call_llm_api(self, prompt: str) -> str:
        # Placeholder for actual API call (OpenAI/Anthropic)
        # In real implementation, this makes network request
        raise NotImplementedError("API call not mocked")

    async def make_decision(self, event: MarketEvent, current_positions: Dict[str, Any]) -> LLMDecision:
        # Construct prompt
        prompt = f"""
        Profile: {self.profile.model_dump_json()}
        Event: {event.model_dump_json()}
        Positions: {json.dumps(current_positions)}
        Output valid JSON only matching LLMDecision schema.
        """
        
        response_text = await self._call_llm_api(prompt)
        
        try:
            decision_dict = json.loads(response_text)
            return LLMDecision(**decision_dict)
        except (json.JSONDecodeError, ValueError) as e:
            # Fallback to HOLD on parsing error
            return LLMDecision(thought=f"Error parsing LLM output: {e}", action="HOLD", symbol=event.symbol)
