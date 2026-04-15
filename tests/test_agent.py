import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime
from src.agent import AgentBrain
from src.models import AgentProfile, MarketEvent, LLMDecision

@pytest.fixture
def profile():
    return AgentProfile(name="Test", personality="Aggressive", risk_tolerance="High", expected_return="50%")

@pytest.mark.asyncio
@patch("src.agent.AgentBrain._call_llm_api")
async def test_agent_brain_decision(mock_call_llm_api, profile):
    # Mock the LLM returning a valid JSON string
    mock_call_llm_api.return_value = '{"thought": "buy it", "action": "BUY", "symbol": "000001.SH", "price_limit": 10.0, "volume": 100}'
    
    agent = AgentBrain(profile=profile, api_key="fake")
    event = MarketEvent(timestamp=datetime.now(), symbol="000001.SH", event_type="TEST", current_price=9.9, features={})
    
    decision = await agent.make_decision(event, current_positions={})
    
    assert isinstance(decision, LLMDecision)
    assert decision.action == "BUY"
    assert decision.volume == 100
