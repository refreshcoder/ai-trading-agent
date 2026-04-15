import asyncio
from datetime import datetime
from typing import Dict, Any
from src.models import MarketEvent


class FilterEngine:
    def __init__(self, event_queue: asyncio.Queue):
        self.event_queue = event_queue

    async def process_raw_data(self, raw_data: Dict[str, Any]):
        symbol = raw_data.get("symbol")
        if not symbol:
            return False

        quote = raw_data.get("quote") or {}
        features = raw_data.get("features") or {}

        price = quote.get("price")
        if price is None:
            return False

        pct_change = quote.get("pct_change")
        volume_ratio = features.get("volume_ratio_20")
        ma20 = features.get("ma20")
        last_close = features.get("last_close")

        event_type = None
        if pct_change is not None and abs(float(pct_change)) >= 1.0:
            event_type = "PCT_MOVE"
        elif volume_ratio is not None and float(volume_ratio) >= 2.0:
            event_type = "VOLUME_SPIKE"
        elif ma20 is not None and last_close is not None and float(last_close) <= float(ma20) < float(price):
            event_type = "MA20_BREAK"

        if event_type is None:
            return False

        ts = raw_data.get("timestamp") or datetime.now()

        event = MarketEvent(
            timestamp=ts,
            symbol=symbol,
            event_type=event_type,
            current_price=float(price),
            features={**features, **quote},
        )
        await self.event_queue.put(event)
        return True
