import asyncio
from datetime import datetime
from typing import Dict, Any
from src.models import MarketEvent


class FilterEngine:
    def __init__(self, event_queue: asyncio.Queue):
        self.event_queue = event_queue

    async def process_raw_data(self, raw_data: Dict[str, Any]):
        # Very simplified mock logic for now
        # In reality, this would maintain state and calculate MAs, etc.
        if raw_data.get("volume", 0) > 10000:
            event = MarketEvent(
                timestamp=datetime.now(),
                symbol=raw_data["symbol"],
                event_type="HIGH_VOLUME",
                current_price=raw_data["price"],
                features={"volume": raw_data["volume"]}
            )
            await self.event_queue.put(event)
