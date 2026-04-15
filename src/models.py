from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any, Literal, Optional


class AgentProfile(BaseModel):
    name: str
    personality: str
    risk_tolerance: str
    expected_return: str


class MarketEvent(BaseModel):
    timestamp: datetime
    symbol: str
    event_type: str
    current_price: float
    features: Dict[str, Any]


class LLMDecision(BaseModel):
    thought: str
    action: Literal["BUY", "SELL", "HOLD"]
    symbol: str
    price_limit: Optional[float] = None
    volume: Optional[int] = None
