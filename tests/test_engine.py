import pytest
import asyncio
from src.engine import FilterEngine
from src.models import MarketEvent


@pytest.mark.asyncio
async def test_filter_engine_triggers_event():
    queue = asyncio.Queue()
    engine = FilterEngine(event_queue=queue)

    raw_data = {
        "symbol": "600519",
        "timestamp": None,
        "quote": {
            "price": 1600.0,
            "pct_change": 1.5,
            "volume": 50000.0,
            "amount": 123.0,
        },
        "features": {"ma20": 1590.0, "last_close": 1585.0},
    }

    await engine.process_raw_data(raw_data)

    event = await queue.get()
    assert isinstance(event, MarketEvent)
    assert event.symbol == "600519"
    assert event.event_type == "PCT_MOVE"
