# A股 AI 交易 Agent 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 开发一个基于轻量级事件驱动架构的 A 股 AI 交易 Agent 服务，包含本地前置行情过滤、大模型决策和模拟盘交易执行。

**Architecture:** 系统分为 Market Feed、Filter Engine、Agent Brain 和 Broker Executor 四个核心组件，通过 `asyncio.Queue` 进行解耦通信。

**Tech Stack:** Python 3.10+, `asyncio`, `pydantic` (数据校验), `pytest` (测试), 大模型 API 客户端 (如 `openai` 或 `anthropic`)。

---

## 阶段 1: 核心数据结构与基础框架搭建

### Task 1: 定义核心数据模型 (Pydantic Models)

**Files:**
- Create: `src/models.py`
- Test: `tests/test_models.py`

- [ ] **Step 1: Write the failing test for models**

```python
# tests/test_models.py
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
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_models.py -v`
Expected: FAIL (ModuleNotFoundError: No module named 'src.models')

- [ ] **Step 3: Write minimal implementation**

```python
# src/models.py
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
```

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_models.py -v`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add src/models.py tests/test_models.py
git commit -m "feat: add core pydantic models for trading agent"
```

### Task 2: 实现模拟盘执行器 (PaperBroker)

**Files:**
- Create: `src/broker.py`
- Test: `tests/test_broker.py`

- [ ] **Step 1: Write the failing test for PaperBroker**

```python
# tests/test_broker.py
import pytest
from src.broker import PaperBroker
from src.models import LLMDecision

@pytest.fixture
def broker():
    return PaperBroker(initial_cash=100000.0)

def test_paper_broker_buy_success(broker):
    decision = LLMDecision(thought="", action="BUY", symbol="000001.SH", price_limit=10.0, volume=100)
    result = broker.execute(decision)
    assert result is True
    assert broker.cash == 99000.0  # 100000 - 1000
    assert broker.positions["000001.SH"]["volume"] == 100

def test_paper_broker_buy_insufficient_funds(broker):
    decision = LLMDecision(thought="", action="BUY", symbol="000001.SH", price_limit=1000.0, volume=200) # needs 200000
    result = broker.execute(decision)
    assert result is False
    assert broker.cash == 100000.0
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_broker.py -v`
Expected: FAIL (ModuleNotFoundError: No module named 'src.broker')

- [ ] **Step 3: Write minimal implementation**

```python
# src/broker.py
from typing import Dict, Any
from src.models import LLMDecision

class BaseBroker:
    def execute(self, decision: LLMDecision) -> bool:
        raise NotImplementedError

class PaperBroker(BaseBroker):
    def __init__(self, initial_cash: float):
        self.cash = initial_cash
        self.positions: Dict[str, Dict[str, Any]] = {} # symbol -> {"volume": int, "avg_price": float}

    def execute(self, decision: LLMDecision) -> bool:
        if decision.action == "BUY":
            if not decision.price_limit or not decision.volume:
                return False
            cost = decision.price_limit * decision.volume
            if self.cash >= cost:
                self.cash -= cost
                if decision.symbol not in self.positions:
                    self.positions[decision.symbol] = {"volume": 0, "avg_price": 0.0}
                # Simplified average price calculation for simulation
                pos = self.positions[decision.symbol]
                total_cost = pos["volume"] * pos["avg_price"] + cost
                pos["volume"] += decision.volume
                pos["avg_price"] = total_cost / pos["volume"]
                return True
            return False
        elif decision.action == "SELL":
            # Simplified sell logic for now
            if decision.symbol in self.positions and self.positions[decision.symbol]["volume"] >= (decision.volume or 0):
                if not decision.price_limit or not decision.volume:
                     return False
                revenue = decision.price_limit * decision.volume
                self.cash += revenue
                self.positions[decision.symbol]["volume"] -= decision.volume
                if self.positions[decision.symbol]["volume"] == 0:
                    del self.positions[decision.symbol]
                return True
            return False
        return True # HOLD
```

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_broker.py -v`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add src/broker.py tests/test_broker.py
git commit -m "feat: implement PaperBroker for simulation trading"
```

## 阶段 2: 核心引擎与大模型集成

### Task 3: 实现本地过滤引擎 (FilterEngine) 基础框架

**Files:**
- Create: `src/engine.py`
- Test: `tests/test_engine.py`

- [ ] **Step 1: Write the failing test for FilterEngine**

```python
# tests/test_engine.py
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
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest -v tests/test_engine.py` (Need `pytest-asyncio` installed)
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
# src/engine.py
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
```

- [ ] **Step 4: Run test to verify it passes**
Run: `pip install pytest-asyncio && pytest -v tests/test_engine.py`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add src/engine.py tests/test_engine.py
git commit -m "feat: implement basic FilterEngine structure"
```

### Task 4: 实现大模型决策大脑 (AgentBrain)

**Files:**
- Create: `src/agent.py`
- Test: `tests/test_agent.py`

- [ ] **Step 1: Write the failing test for AgentBrain**

```python
# tests/test_agent.py
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
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest -v tests/test_agent.py`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
# src/agent.py
import json
from typing import Dict, Any
from src.models import AgentProfile, MarketEvent, LLMDecision

class AgentBrain:
    def __init__(self, profile: AgentProfile, api_key: str):
        self.profile = profile
        self.api_key = api_key

    async def _call_llm_api(self, prompt: str) -> str:
        # Placeholder for actual API call (OpenAI/Anthropic)
        # In real implementation, this makes network request
        raise NotImplementedError("API call not mocked")

    async def make_decision(self, event: MarketEvent, current_positions: Dict[str, Any]) -> LLMDecision:
        # Construct prompt
        prompt = f"""
        Profile: {self.profile.model_dump_json()}
        Event: {event.model_dump_json()}
        Positions: {json.dumps(current_positions)}
        Output valid JSON only matching LLMDecision schema.
        """
        
        response_text = await self._call_llm_api(prompt)
        
        try:
            decision_dict = json.loads(response_text)
            return LLMDecision(**decision_dict)
        except (json.JSONDecodeError, ValueError) as e:
            # Fallback to HOLD on parsing error
            return LLMDecision(thought=f"Error parsing LLM output: {e}", action="HOLD", symbol=event.symbol)
```

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest -v tests/test_agent.py`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add src/agent.py tests/test_agent.py
git commit -m "feat: implement AgentBrain with LLM decision parsing"
```

## 阶段 3: 主流程串联

### Task 5: 实现主调度循环 (Main Orchestrator)

**Files:**
- Create: `src/main.py`
- Modify: `src/engine.py` (if needed for mock feed)

- [ ] **Step 1: Write the basic orchestrator structure (no explicit unit test, integration focus)**

```python
# src/main.py
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
            
            # Mock the internal LLM call for this integration script
            brain._call_llm_api = asyncio.coroutine(lambda p: '{"thought": "mock", "action": "BUY", "symbol": "600519.SH", "price_limit": 1605.0, "volume": 100}')
            
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
```

- [ ] **Step 2: Run the main script**
Run: `python src/main.py`
Expected: Output showing events received, decisions made, and broker execution success.

- [ ] **Step 3: Commit**
```bash
git add src/main.py
git commit -m "feat: wire up main orchestrator with async queue"
```
