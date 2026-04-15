from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Protocol, Sequence


@dataclass(frozen=True)
class SpotQuote:
    symbol: str
    ts: datetime
    price: float
    pct_change: float | None
    volume: float | None
    amount: float | None


@dataclass(frozen=True)
class MinuteBar:
    ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float | None
    amount: float | None


class MarketDataProvider(Protocol):
    def get_spot(self, symbols: Sequence[str]) -> Dict[str, SpotQuote]:
        ...

    def get_minute_kline(self, symbol: str, start: datetime, end: datetime) -> List[MinuteBar]:
        ...

