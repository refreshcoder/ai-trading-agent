import pytest
from datetime import datetime
from src.models import AgentProfile, MarketEvent, LLMDecision

def test_agent_profile_validation():
    profile = AgentProfile(
        name="Test",
        personality="稳健",
        risk_tolerance="低",
        expected_return="10%"
    )
    assert profile.name == "Test"

def test_market_event_validation():
    event = MarketEvent(
        timestamp=datetime.now(),
        symbol="600519.SH",
        event_type="BREAKOUT",
        current_price=1500.0,
        features={"ma5": 1490.0}
    )
    assert event.symbol == "600519.SH"

def test_llm_decision_validation():
    decision = LLMDecision(
        thought="looks good",
        action="BUY",
        symbol="600519.SH",
        price_limit=1505.0,
        volume=100
    )
    assert decision.action == "BUY"
