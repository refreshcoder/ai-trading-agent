from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, time
from typing import Dict, List, Tuple

from src.features import compute_features
from src.providers.base import MarketDataProvider, SpotQuote
from src.engine import FilterEngine

TradingSession = Tuple[time, time]


def _is_in_sessions(now_t: time, sessions: Tuple[TradingSession, TradingSession]) -> bool:
    for start, end in sessions:
        if start <= now_t <= end:
            return True
    return False


@dataclass
class MarketFeed:
    provider: MarketDataProvider
    symbols: List[str]
    engine: FilterEngine
    spot_poll_interval_sec: int
    kline_refresh_interval_sec: int
    strict_trading_sessions: bool
    trade_sessions: Tuple[TradingSession, TradingSession]

    _features_cache: Dict[str, Dict[str, float]] = None  # type: ignore
    _last_kline_refresh: datetime | None = None

    def __post_init__(self) -> None:
        if self._features_cache is None:
            self._features_cache = {}

    def _need_refresh_kline(self, now: datetime) -> bool:
        if self._last_kline_refresh is None:
            return True
        return (now - self._last_kline_refresh).total_seconds() >= self.kline_refresh_interval_sec

    def refresh_kline_cache(self, now: datetime) -> None:
        end = now
        start = end - timedelta(minutes=120)
        for s in self.symbols:
            bars = self.provider.get_minute_kline(s, start=start, end=end)
            self._features_cache[s] = compute_features(bars)
        self._last_kline_refresh = now

    async def poll_spot_and_process(self, now: datetime) -> int:
        quotes = self.provider.get_spot(self.symbols)
        triggered = 0
        for s in self.symbols:
            q: SpotQuote | None = quotes.get(s)
            if q is None:
                continue
            raw_data = {
                "symbol": s,
                "timestamp": q.ts,
                "quote": {
                    "price": q.price,
                    "pct_change": q.pct_change,
                    "volume": q.volume,
                    "amount": q.amount,
                },
                "features": self._features_cache.get(s, {}),
            }
            if await self.engine.process_raw_data(raw_data):
                triggered += 1
        return triggered

    async def run(self, max_loops: int) -> None:
        loops = 0
        while True:
            now = datetime.now()
            if self.strict_trading_sessions and not _is_in_sessions(now.time(), self.trade_sessions):
                await asyncio.sleep(60)
                continue

            if self._need_refresh_kline(now):
                self.refresh_kline_cache(now)

            await self.poll_spot_and_process(now)

            loops += 1
            if max_loops > 0 and loops >= max_loops:
                break
            await asyncio.sleep(self.spot_poll_interval_sec)
