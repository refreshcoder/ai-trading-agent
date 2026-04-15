from typing import Dict, Any
from src.models import LLMDecision


class BaseBroker:
    def execute(self, decision: LLMDecision) -> bool:
        raise NotImplementedError


class PaperBroker(BaseBroker):
    def __init__(self, initial_cash: float):
        self.cash = initial_cash
        # symbol -> {"volume": int, "avg_price": float}
        self.positions: Dict[str, Dict[str, Any]] = {}

    def execute(self, decision: LLMDecision) -> bool:
        if decision.action == "BUY":
            if not decision.price_limit or not decision.volume:
                return False
            cost = decision.price_limit * decision.volume
            if self.cash >= cost:
                self.cash -= cost
                if decision.symbol not in self.positions:
                    self.positions[decision.symbol] = {
                        "volume": 0, "avg_price": 0.0}
                # Simplified average price calculation for simulation
                pos = self.positions[decision.symbol]
                total_cost = pos["volume"] * pos["avg_price"] + cost
                pos["volume"] += decision.volume
                pos["avg_price"] = total_cost / pos["volume"]
                return True
            return False
        elif decision.action == "SELL":
            # Simplified sell logic for now
            if (decision.symbol in self.positions and
                    self.positions[decision.symbol]["volume"] >=
                    (decision.volume or 0)):
                if not decision.price_limit or not decision.volume:
                    return False
                revenue = decision.price_limit * decision.volume
                self.cash += revenue
                self.positions[decision.symbol]["volume"] -= decision.volume
                if self.positions[decision.symbol]["volume"] == 0:
                    del self.positions[decision.symbol]
                return True
            return False
        return True  # HOLD
