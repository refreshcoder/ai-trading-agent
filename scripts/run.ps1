Param(
  [string]$Provider = "offline"
)

$ErrorActionPreference = "Stop"
$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $RootDir

function Get-PythonCmd {
  $py = (Get-Command py -ErrorAction SilentlyContinue)
  if ($null -ne $py) { return @("py", "-3") }
  $python = (Get-Command python -ErrorAction SilentlyContinue)
  if ($null -ne $python) { return @("python") }
  throw "Python not found. Please install Python >= 3.12."
}

$PythonCmd = Get-PythonCmd
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
$env:SYMBOLS = $(if ($env:SYMBOLS) { $env:SYMBOLS } else { "600519" })
$env:SPOT_POLL_INTERVAL_SEC = $(if ($env:SPOT_POLL_INTERVAL_SEC) { $env:SPOT_POLL_INTERVAL_SEC } else { "1" })
$env:KLINE_REFRESH_INTERVAL_SEC = $(if ($env:KLINE_REFRESH_INTERVAL_SEC) { $env:KLINE_REFRESH_INTERVAL_SEC } else { "1" })
$env:MAX_LOOPS = $(if ($env:MAX_LOOPS) { $env:MAX_LOOPS } else { "1" })
$env:STRICT_TRADING_SESSIONS = $(if ($env:STRICT_TRADING_SESSIONS) { $env:STRICT_TRADING_SESSIONS } else { "false" })

& $VenvPy "src\main.py"

