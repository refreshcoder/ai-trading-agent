from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Sequence

import pandas as pd

from src.providers.base import MinuteBar, SpotQuote


def _pick_float(row, key: str) -> float | None:
    if key not in row:
        return None
    v = row[key]
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except Exception:
        pass
    try:
        return float(v)
    except Exception:
        return None


class AkShareProvider:
    def __init__(self):
        import akshare as ak  # type: ignore

        self._ak = ak

    def get_spot(self, symbols: Sequence[str]) -> Dict[str, SpotQuote]:
        if not symbols:
            return {}

        df = self._ak.stock_zh_a_spot_em()
        if df is None or df.empty:
            return {}

        symbol_set = set(symbols)
        now = datetime.now()
        out: Dict[str, SpotQuote] = {}

        for _, r in df.iterrows():
            code = str(r.get("代码", "")).strip()
            if code not in symbol_set:
                continue
            price = _pick_float(r, "最新价")
            if price is None:
                continue
            out[code] = SpotQuote(
                symbol=code,
                ts=now,
                price=price,
                pct_change=_pick_float(r, "涨跌幅"),
                volume=_pick_float(r, "成交量"),
                amount=_pick_float(r, "成交额"),
            )

        return out

    def get_minute_kline(self, symbol: str, start: datetime, end: datetime) -> List[MinuteBar]:
        start_s = start.strftime("%Y-%m-%d %H:%M:%S")
        end_s = end.strftime("%Y-%m-%d %H:%M:%S")

        df = self._ak.stock_zh_a_hist_min_em(
            symbol=symbol,
            period="1",
            start_date=start_s,
            end_date=end_s,
            adjust="",
        )
        if df is None or df.empty:
            return []

        out: List[MinuteBar] = []
        for _, r in df.iterrows():
            ts_raw = r.get("时间")
            try:
                ts = pd.to_datetime(ts_raw).to_pydatetime()
            except Exception:
                continue
            o = _pick_float(r, "开盘")
            h = _pick_float(r, "最高")
            l = _pick_float(r, "最低")
            c = _pick_float(r, "收盘")
            if o is None or h is None or l is None or c is None:
                continue
            out.append(
                MinuteBar(
                    ts=ts,
                    open=o,
                    high=h,
                    low=l,
                    close=c,
                    volume=_pick_float(r, "成交量"),
                    amount=_pick_float(r, "成交额"),
                )
            )

        return out

