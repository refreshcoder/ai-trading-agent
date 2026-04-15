import os
from dataclasses import dataclass
from datetime import time
from typing import Iterable, List, Optional, Tuple


def load_dotenv(path: str = ".env") -> None:
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def _parse_int(value: Optional[str], default: int) -> int:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _parse_float(value: Optional[str], default: float) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _parse_bool(value: Optional[str], default: bool) -> bool:
    if value is None or value == "":
        return default
    v = value.strip().lower()
    if v in {"1", "true", "yes", "y", "on"}:
        return True
    if v in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _parse_symbols(value: Optional[str]) -> List[str]:
    if not value:
        return []
    parts = [p.strip() for p in value.replace(";", ",").split(",")]
    return [p for p in parts if p]


def _normalize_symbol(symbol: str) -> str:
    s = symbol.strip().upper()
    for suffix in [".SH", ".SZ", ".BJ"]:
        if s.endswith(suffix):
            s = s[: -len(suffix)]
            break
    return s


def normalize_symbols(symbols: Iterable[str]) -> List[str]:
    out: List[str] = []
    for s in symbols:
        if not s:
            continue
        out.append(_normalize_symbol(s))
    return out


TradingSession = Tuple[time, time]


@dataclass(frozen=True)
class AppConfig:
    provider: str
    symbols: List[str]
    spot_poll_interval_sec: int
    kline_refresh_interval_sec: int
    initial_cash: float
    max_loops: int
    strict_trading_sessions: bool
    trade_sessions: Tuple[TradingSession, TradingSession]


def load_config(dotenv_path: str = ".env") -> AppConfig:
    load_dotenv(dotenv_path)

    provider = os.getenv("DATA_PROVIDER", "offline").strip().lower()
    symbols = normalize_symbols(_parse_symbols(os.getenv("SYMBOLS")))

    spot_poll_interval_sec = _parse_int(os.getenv("SPOT_POLL_INTERVAL_SEC"), 30)
    kline_refresh_interval_sec = _parse_int(
        os.getenv("KLINE_REFRESH_INTERVAL_SEC"), 300
    )
    initial_cash = _parse_float(os.getenv("INITIAL_CASH"), 500000.0)
    max_loops = _parse_int(os.getenv("MAX_LOOPS"), 3)
    strict_trading_sessions = _parse_bool(os.getenv("STRICT_TRADING_SESSIONS"), True)

    trade_sessions: Tuple[TradingSession, TradingSession] = (
        (time(9, 30), time(11, 30)),
        (time(13, 0), time(15, 0)),
    )

    return AppConfig(
        provider=provider,
        symbols=symbols,
        spot_poll_interval_sec=spot_poll_interval_sec,
        kline_refresh_interval_sec=kline_refresh_interval_sec,
        initial_cash=initial_cash,
        max_loops=max_loops,
        strict_trading_sessions=strict_trading_sessions,
        trade_sessions=trade_sessions,
    )
