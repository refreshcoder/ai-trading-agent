import asyncio
from src.models import AgentProfile
from src.broker import PaperBroker
from src.engine import FilterEngine
from src.agent import AgentBrain

async def mock_market_feed(engine: FilterEngine):
    """Simulates incoming market data ticks"""
    for _ in range(3):
        await asyncio.sleep(0.1)
        await engine.process_raw_data({"symbol": "600519.SH", "price": 1600.0, "volume": 15000})

async def agent_worker(queue: asyncio.Queue, brain: AgentBrain, broker: PaperBroker):
    """Listens to queue and makes decisions"""
    while True:
        try:
            event = await asyncio.wait_for(queue.get(), timeout=1.0)
            print(f"Agent received event: {event.event_type} for {event.symbol}")
            
            async def mock_call(p):
                return '{"thought": "mock", "action": "BUY", "symbol": "600519.SH", "price_limit": 1605.0, "volume": 100}'
            brain._call_llm_api = mock_call
            
            decision = await brain.make_decision(event, broker.positions)
            print(f"Agent decided: {decision.action} {decision.volume} shares")
            
            success = broker.execute(decision)
            print(f"Broker execution success: {success}, Cash left: {broker.cash}")
            queue.task_done()
        except asyncio.TimeoutError:
            break # Exit loop after timeout for testing purposes

async def main():
    event_queue = asyncio.Queue()
    broker = PaperBroker(initial_cash=500000.0)
    engine = FilterEngine(event_queue)
    
    profile = AgentProfile(name="MainBot", personality="Test", risk_tolerance="Low", expected_return="10%")
    brain = AgentBrain(profile=profile, api_key="dummy")

    # Run feed and worker concurrently
    await asyncio.gather(
        mock_market_feed(engine),
        agent_worker(event_queue, brain, broker)
    )
    print("Simulation finished.")

if __name__ == "__main__":
    asyncio.run(main())
