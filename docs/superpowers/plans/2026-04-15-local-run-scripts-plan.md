# Local Run Scripts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 提供跨平台一键运行脚本（macOS/Linux + Windows），自动创建 venv、安装依赖、补齐 .env，并以离线模式执行一次项目运行测试。

**Architecture:** 在 `scripts/` 下增加 Bash 与 PowerShell 两个入口脚本；脚本仅负责环境检测与启动参数拼装，不改动核心业务逻辑。

**Tech Stack:** Bash、PowerShell、Python 3.12+、venv、pip

---

### Task 1: 增加脚本目录与 Bash 运行脚本

**Files:**
- Create: `scripts/run.sh`

- [ ] **Step 1: Create scripts/run.sh**

```bash
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
```

- [ ] **Step 2: Verify script syntax quickly**

Run: `bash -n scripts/run.sh`
Expected: exit code 0

- [ ] **Step 3: Commit**

```bash
git add scripts/run.sh
git commit -m "chore: add unix run script"
```

### Task 2: 增加 PowerShell 运行脚本

**Files:**
- Create: `scripts/run.ps1`

- [ ] **Step 1: Create scripts/run.ps1**

```powershell
Param(
  [string]$Provider = "offline"
)

$ErrorActionPreference = "Stop"
$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $RootDir

function Get-PythonPath {
  $py = (Get-Command py -ErrorAction SilentlyContinue)
  if ($null -ne $py) { return "py -3" }
  $python = (Get-Command python -ErrorAction SilentlyContinue)
  if ($null -ne $python) { return "python" }
  throw "Python not found. Please install Python >= 3.12."
}

$PythonCmd = Get-PythonPath
$PyVer = & $PythonCmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ([version]$PyVer -lt [version]"3.12") {
  throw "Python >= 3.12 required, got $PyVer"
}

if (-not (Test-Path ".venv")) {
  & $PythonCmd -m venv .venv
}

$VenvPy = ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPy)) {
  throw ".venv is invalid. Remove .venv and rerun."
}

& $VenvPy -m pip install --upgrade pip
& $VenvPy -m pip install -r requirements.txt

if (-not (Test-Path ".env") -and (Test-Path ".env.example")) {
  Copy-Item ".env.example" ".env"
}

$env:PYTHONPATH = "."
$env:DATA_PROVIDER = $Provider
$env:SYMBOLS = $env:SYMBOLS ?? "600519"
$env:SPOT_POLL_INTERVAL_SEC = $env:SPOT_POLL_INTERVAL_SEC ?? "1"
$env:KLINE_REFRESH_INTERVAL_SEC = $env:KLINE_REFRESH_INTERVAL_SEC ?? "1"
$env:MAX_LOOPS = $env:MAX_LOOPS ?? "1"
$env:STRICT_TRADING_SESSIONS = $env:STRICT_TRADING_SESSIONS ?? "false"

& $VenvPy "src\main.py"
```

- [ ] **Step 2: Commit**

```bash
git add scripts/run.ps1
git commit -m "chore: add windows run script"
```

### Task 3: 更新忽略规则与 README

**Files:**
- Modify: `.gitignore`
- Modify: `README.md`

- [ ] **Step 1: Update .gitignore to ignore venv**

Add line:

```gitignore
.venv/
```

- [ ] **Step 2: Update README with one-command usage**

Add section:

```markdown
## 一键运行

macOS/Linux:

```bash
bash scripts/run.sh
```

Windows (PowerShell):

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run.ps1
```
```

- [ ] **Step 3: Commit**

```bash
git add .gitignore README.md
git commit -m "docs: add one-command local run instructions"
```

### Task 4: 本地验证并推送

**Files:**
- Modify: (none)

- [ ] **Step 1: Run unit tests**

Run: `PYTHONPATH=. pytest tests/ -v`
Expected: PASS

- [ ] **Step 2: Run unix script in offline mode**

Run: `bash scripts/run.sh`
Expected: exit code 0

- [ ] **Step 3: Push**

Run:

```bash
git push origin master
```

