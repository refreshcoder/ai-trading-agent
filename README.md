# A股 AI 交易 Agent

## 简介
这是一个基于轻量级事件驱动架构的 A 股 AI 交易 Agent 服务，包含本地前置行情过滤、大模型决策和模拟盘交易执行。

## 架构
系统分为四个核心组件，通过 `asyncio.Queue` 进行解耦通信：
- **Market Feed**: 负责获取实时行情数据
- **Filter Engine**: 本地前置过滤引擎，根据指标触发事件
- **Agent Brain**: 接收事件，调用大模型做出决策
- **Broker Executor**: 模拟盘执行器，处理买卖逻辑和持仓记录

## 运行
```bash
pip install -r requirements.txt
cp .env.example .env
PYTHONPATH=. python src/main.py
```

## 测试
```bash
PYTHONPATH=. pytest tests/ -v
```
