import asyncio
import json

from src.agent import AgentBrain
from src.broker import PaperBroker
from src.config import load_config
from src.engine import FilterEngine
from src.market_feed import MarketFeed
from src.models import AgentProfile
from src.providers.offline_provider import OfflineProvider


def build_provider(name: str):
    n = (name or "").strip().lower()
    if n == "akshare":
        from src.providers.akshare_provider import AkShareProvider

        return AkShareProvider()
    if n == "offline":
        return OfflineProvider()
    raise ValueError(f"Unsupported provider: {name}")


async def main():
    cfg = load_config()
    symbols = cfg.symbols or ["600519"]

    event_queue: asyncio.Queue = asyncio.Queue()
    broker = PaperBroker(initial_cash=cfg.initial_cash)
    engine = FilterEngine(event_queue=event_queue)

    profile = AgentProfile(
        name="MainBot",
        personality="Test",
        risk_tolerance="Low",
        expected_return="10%",
    )
    brain = AgentBrain(profile=profile, api_key="dummy")

    async def mock_call_llm_api(prompt: str) -> str:
        return json.dumps(
            {
                "thought": "mock",
                "action": "HOLD",
                "symbol": symbols[0],
            }
        )

    brain._call_llm_api = mock_call_llm_api

    provider = build_provider(cfg.provider)
    feed = MarketFeed(
        provider=provider,
        symbols=symbols,
        engine=engine,
        spot_poll_interval_sec=cfg.spot_poll_interval_sec,
        kline_refresh_interval_sec=cfg.kline_refresh_interval_sec,
        strict_trading_sessions=cfg.strict_trading_sessions,
        trade_sessions=cfg.trade_sessions,
    )

    done = asyncio.Event()

    async def run_feed():
        await feed.run(max_loops=cfg.max_loops)
        done.set()

    async def run_agent():
        while True:
            if done.is_set() and event_queue.empty():
                break
            try:
                event = await asyncio.wait_for(event_queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            decision = await brain.make_decision(event, broker.positions)
            broker.execute(decision)
            event_queue.task_done()

    await asyncio.gather(run_feed(), run_agent())


if __name__ == "__main__":
    asyncio.run(main())
