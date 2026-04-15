#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PROVIDER="offline"
if [[ "${1:-}" == "--provider" && -n "${2:-}" ]]; then
  PROVIDER="$2"
  shift 2
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 not found. Please install Python >= 3.12." >&2
  exit 1
fi

PYTHON_BIN="python3"
PY_VER="$("$PYTHON_BIN" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
REQ_VER="3.12"
if [[ "$(printf '%s\n' "$REQ_VER" "$PY_VER" | sort -V | head -n1)" != "$REQ_VER" ]]; then
  echo "Python >= 3.12 required, got $PY_VER" >&2
  exit 1
fi

if [[ ! -d ".venv" ]]; then
  "$PYTHON_BIN" -m venv .venv
fi

VENV_PY=".venv/bin/python"
if [[ ! -x "$VENV_PY" ]]; then
  echo ".venv is invalid. Remove .venv and rerun." >&2
  exit 1
fi

"$VENV_PY" -m pip install --upgrade pip
"$VENV_PY" -m pip install -r requirements.txt

if [[ ! -f ".env" && -f ".env.example" ]]; then
  cp .env.example .env
fi

export PYTHONPATH=.
export DATA_PROVIDER="$PROVIDER"
export SYMBOLS="${SYMBOLS:-600519}"
export SPOT_POLL_INTERVAL_SEC="${SPOT_POLL_INTERVAL_SEC:-1}"
export KLINE_REFRESH_INTERVAL_SEC="${KLINE_REFRESH_INTERVAL_SEC:-1}"
export MAX_LOOPS="${MAX_LOOPS:-1}"
export STRICT_TRADING_SESSIONS="${STRICT_TRADING_SESSIONS:-false}"

"$VENV_PY" src/main.py

