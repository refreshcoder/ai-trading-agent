import pytest
import asyncio
from src.engine import FilterEngine
from src.models import MarketEvent

@pytest.mark.asyncio
async def test_filter_engine_triggers_event():
    queue = asyncio.Queue()
    engine = FilterEngine(event_queue=queue)
    
    # Mock raw data feed
    raw_data = {"symbol": "600519.SH", "price": 1600.0, "volume": 50000}
    
    await engine.process_raw_data(raw_data)
    
    # Should trigger an event because volume is high (mock condition)
    event = await queue.get()
    assert isinstance(event, MarketEvent)
    assert event.symbol == "600519.SH"
    assert event.event_type == "HIGH_VOLUME"
