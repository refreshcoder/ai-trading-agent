# A股 AI 交易 Agent 系统设计文档

## 1. 概述 (Overview)

本项目旨在开发一款调用大语言模型（LLM）进行 A 股股票交易的自动化服务。该服务能够根据预设的性格、风险承受能力和收益预期，制定投资策略；通过实时流式获取市场行情与新闻资讯，在开盘期间进行快速分析，并最终在模拟盘中执行交易操作。

系统设计的核心理念是：**“轻量级事件驱动 + 本地前置过滤”**，以在保证系统实时响应市场异动的同时，最大程度地降低大模型的 Token 消耗成本。

## 2. 核心需求 (Requirements)

1.  **市场适配**：主要针对 A 股市场（需考虑 T+1、涨跌幅限制等规则）。
2.  **交易执行**：开发阶段实现模拟盘（Paper Trading），系统需预留 `Broker` 接口，以便未来无缝切换至实盘（如 QMT/Ptrade）。
3.  **信息处理**：现阶段采用**结构化数据主导**模式。后台服务负责抓取行情和新闻，提取关键特征（如均线、资金流向、情感得分）喂给大模型进行决策；预留 `ResearchAgent` 接口以支持未来向全文检索的混合模式扩展。
4.  **架构设计**：采用基于 `asyncio` 的事件驱动架构。本地脚本负责高频轮询或订阅行情流进行前置过滤，仅在触发预设条件（如异动突破）或定时节点时，才唤醒 Agent 进行决策，避免无意义的 Token 消耗。

## 3. 系统架构设计 (Architecture)

系统采用模块化的异步事件驱动架构，核心组件通过 `asyncio.Queue` 进行解耦通信。

### 3.1 核心组件 (Core Components)

*   **Market Feed (行情与资讯源)**
    *   **职责**：负责从免费或商业 API（如新浪财经、Tushare、聚宽数据等）流式或高频定时获取 A 股的实时行情（Tick/K线）及相关新闻标题。
*   **Filter Engine (前置过滤引擎 - 本地运行)**
    *   **职责**：接收 Market Feed 的原始数据，计算技术指标（如 MA、MACD、RSI）和基础面特征。当数据满足预设的“关注条件”（如：价格突破均线、交易量激增、出现相关重大新闻）时，生成一个 `MarketEvent` 结构化事件对象，并推入事件队列。
    *   **优势**：拦截绝大部分无效或平庸的行情时间，保护大模型不被垃圾信息淹没，极大地节省 Token。
*   **Event Queue (事件队列)**
    *   **职责**：基于 `asyncio.Queue` 的轻量级内存消息总线，连接过滤引擎和 Agent 决策中心。
*   **Agent Brain (LLM 决策大脑)**
    *   **职责**：异步监听事件队列。当收到 `MarketEvent` 时，将其与当前的“Agent Profile（性格、风险偏好、收益预期）”及“持仓状态（Positions）”组装成 Prompt。调用大语言模型（如 GPT-4、Claude 3 或本地部署模型），要求输出包含交易指令的 JSON 结构。
*   **Broker Executor (交易执行器)**
    *   **职责**：解析 Agent 的决策输出。如果是买卖指令，则调用底层交易接口。
    *   **抽象**：定义 `BaseBroker` 接口。当前实现 `PaperBroker`（本地记录资金与持仓，模拟撮合），未来扩展 `RealBroker`（对接 QMT/Ptrade）。

### 3.2 数据流转过程 (Data Flow)

1.  **开盘期间**，`Market Feed` 每隔 N 秒拉取一次关注股票池的最新数据。
2.  `Filter Engine` 更新本地指标缓存，判断是否触发异动。
3.  若无异动，丢弃数据，等待下一轮；若有异动（例如某股票放量突破），生成 `MarketEvent(symbol="600519", type="PRICE_BREAKOUT", data={...})`。
4.  `MarketEvent` 被推入 `Event Queue`。
5.  休眠中的 `Agent Brain` 被唤醒，取出事件，组装 Prompt 提交给 LLM。
6.  LLM 结合其设定的性格（如“稳健型”），判断该异动是否值得追涨，输出 `{"action": "BUY", "symbol": "600519", "volume": 100, "reason": "..."}`。
7.  `Broker Executor` 收到指令，在模拟盘中扣除可用资金，增加持仓记录。

## 4. 接口与数据结构定义 (Interfaces & Structures)

### 4.1 Agent Profile (性格配置)
```json
{
  "name": "SteadyTrader_01",
  "personality": "稳健型，偏好右侧交易，对利空新闻极度敏感",
  "risk_tolerance": "低，单只股票仓位不超过总资金的 15%",
  "expected_return": "年化 15%"
}
```

### 4.2 Market Event (市场事件)
```json
{
  "timestamp": "2024-05-20T10:30:00Z",
  "symbol": "600519.SH",
  "event_type": "TECHNICAL_BREAKOUT",
  "current_price": 1700.5,
  "features": {
    "ma5": 1680.2,
    "volume_ratio": 2.5,
    "latest_news_sentiment": 0.8
  }
}
```

### 4.3 LLM Decision Output (大模型决策输出)
```json
{
  "thought": "该股票突破 MA5 且量比放大，当前性格设定允许在确立趋势后进行右侧追涨，且最新新闻情感偏正面。",
  "action": "BUY",
  "symbol": "600519.SH",
  "price_limit": 1705.0,
  "volume": 100
}
```

## 5. 错误处理与容灾 (Error Handling)

1.  **API 熔断/限流**：如果大模型 API 响应超时或被限流，事件应被重新放回队列或记录在死信队列（Dead Letter Queue）中，同时 `Broker Executor` 默认采取“不操作（Hold）”策略。
2.  **幻觉防护**：在将 LLM 输出传递给 Broker 之前，必须在本地进行**硬性规则校验**。例如：检查可用资金是否充足、买入数量是否为 100 的整数倍（A 股规则）、买入价格是否超过涨停板。若校验失败，直接拦截并丢弃该指令。

## 6. 测试与验证策略 (Testing Strategy)

1.  **历史回测 (Backtesting)**：编写一个历史数据重放工具（Replayer），将过去某段时间的 A 股 Tick 数据和历史新闻注入 `Market Feed`，快速运行系统，验证 Agent 在历史行情中的收益率和交易逻辑是否符合其性格设定。
2.  **单元测试**：重点测试 `Filter Engine` 的指标计算准确性，以及 `Broker Executor` 的规则校验（特别是 A 股特有的 T+1 限制和资金校验）。
