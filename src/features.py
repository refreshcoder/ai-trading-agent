from __future__ import annotations

from typing import Dict, List

from src.providers.base import MinuteBar


def compute_features(bars: List[MinuteBar]) -> Dict[str, float]:
    if not bars:
        return {}

    closes = [b.close for b in bars]
    volumes = [b.volume or 0.0 for b in bars]

    def ma(n: int) -> float:
        if len(closes) < n:
            return sum(closes) / len(closes)
        return sum(closes[-n:]) / n

    def ret(n: int) -> float:
        if len(closes) <= n:
            return 0.0
        prev = closes[-n - 1]
        if prev == 0:
            return 0.0
        return (closes[-1] - prev) / prev * 100.0

    def vol_ratio(n: int) -> float:
        if not volumes:
            return 0.0
        cur = volumes[-1]
        if len(volumes) < n:
            avg = sum(volumes) / len(volumes)
        else:
            avg = sum(volumes[-n:]) / n
        if avg == 0:
            return 0.0
        return cur / avg

    return {
        "ma5": ma(5),
        "ma20": ma(20),
        "ret_1m": ret(1),
        "ret_5m": ret(5),
        "ret_15m": ret(15),
        "volume_ratio_20": vol_ratio(20),
        "last_close": closes[-1],
    }

