# AkShare MarketFeed v0.2 设计

## 目标

- 用 AkShare 接入 A 股真实行情数据源
- 同时支持：
  - 实时快照轮询：用于事件触发（30 秒一次）
  - 1 分钟 K 线：用于特征计算（5 分钟一次刷新缓存）
- 股票池采用自选列表（配置项）
- 严格按 A 股交易时段运行（9:30-11:30，13:00-15:00；其余时间休眠）

## 非目标（v0.2 不做）

- 新闻/研报/舆情接入与情绪打分
- 复杂风控（最大回撤、分级止损、手续费/滑点模型等）
- LLM 真实调用（保留接口，运行链路用固定决策或 mock）

## 架构与模块边界

### 新增模块

- `src/config.py`
  - 加载 `.env`（如果存在）与环境变量
  - 解析股票池、轮询间隔、K 线刷新间隔、数据源选择等
- `src/providers/base.py`
  - 定义行情数据源的抽象接口（便于未来替换）
- `src/providers/akshare_provider.py`
  - AkShare 实现：批量快照、单标的分钟 K 线
  - 输出规范化后的字段结构（不直接向上层暴露 AkShare 列名）
- `src/providers/offline_provider.py`
  - 离线实现：返回稳定的快照与分钟 K，用于 CI/本地无网络的“项目运行测试”
- `src/features.py`
  - 从分钟 K 线计算结构化特征（MA、近 N 分钟收益率、量比等最小集合）
- `src/market_feed.py`
  - 主行情循环：按交易时段调度
  - 30 秒轮询快照（读取最新价/成交量/涨跌幅等）
  - 5 分钟刷新分钟 K 缓存，并计算特征缓存

### 修改模块

- `src/engine.py`
  - 从简单阈值触发升级为基于快照 + 特征的触发规则
  - `process_raw_data()` 接收包含 `quote` 与 `features` 的结构化输入，输出 `MarketEvent`
- `src/main.py`
  - 替换 `mock_market_feed()` 为真实 `MarketFeed`
  - 运行链路默认使用离线 provider（CI 稳定），可通过环境变量切换到 AkShare

## 数据流

1. `MarketFeed` 根据配置生成股票池
2. 每 5 分钟刷新每只股票的 1 分钟 K 线数据并计算特征缓存
3. 每 30 秒轮询快照并组合为 `raw_data={symbol, quote, features}`
4. 将 `raw_data` 交给 `FilterEngine.process_raw_data()`，满足规则则推送 `MarketEvent` 到 `asyncio.Queue`
5. 下游 worker（Agent）消费事件并产生决策（v0.2 可固定 HOLD 或 mock）
6. `PaperBroker` 执行决策（v0.2 以链路跑通为主）

## 错误处理

- AkShare 拉取失败：
  - 单次失败不终止进程，记录错误并跳过该轮
  - 连续失败可触发退避（v0.2 先做固定短退避）
- 数据缺失/列名变化：
  - Provider 层做容错映射，缺失字段返回 `None` 并由上层策略决定是否忽略

## 可测性

- 离线 provider 保证 `python src/main.py` 在无网络、无 AkShare 的环境中可运行
- GitHub Actions 的手动 workflow 默认使用离线 provider，确保运行测试稳定
