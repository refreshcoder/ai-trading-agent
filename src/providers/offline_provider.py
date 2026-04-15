from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List, Sequence

from src.providers.base import MinuteBar, SpotQuote


class OfflineProvider:
    def __init__(self):
        self._base_price: Dict[str, float] = {}

    def get_spot(self, symbols: Sequence[str]) -> Dict[str, SpotQuote]:
        now = datetime.now()
        out: Dict[str, SpotQuote] = {}
        for i, s in enumerate(symbols):
            base = self._base_price.get(s)
            if base is None:
                base = 10.0 + i
                self._base_price[s] = base
            price = base + (now.second % 10) * 0.01
            out[s] = SpotQuote(
                symbol=s,
                ts=now,
                price=price,
                pct_change=0.1,
                volume=10000.0 + i * 100,
                amount=price * (10000.0 + i * 100),
            )
        return out

    def get_minute_kline(self, symbol: str, start: datetime, end: datetime) -> List[MinuteBar]:
        base = self._base_price.get(symbol, 10.0)
        bars: List[MinuteBar] = []
        t = start.replace(second=0, microsecond=0)
        while t <= end:
            m = int((t - start).total_seconds() // 60)
            close = base + (m % 20) * 0.02
            open_ = close - 0.01
            high = close + 0.02
            low = open_ - 0.02
            vol = 1000.0 + (m % 10) * 50
            bars.append(
                MinuteBar(
                    ts=t,
                    open=open_,
                    high=high,
                    low=low,
                    close=close,
                    volume=vol,
                    amount=vol * close,
                )
            )
            t += timedelta(minutes=1)
        return bars

