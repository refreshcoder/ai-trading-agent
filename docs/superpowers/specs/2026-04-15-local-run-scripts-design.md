# 本地一键运行脚本设计

## 目标

- 解决用户 clone 仓库到本机后，Python 环境与依赖导致无法运行的问题
- 提供跨平台“一键运行”脚本：
  - macOS/Linux：`scripts/run.sh`
  - Windows：`scripts/run.ps1`
- 使用 `venv` 隔离依赖
- 本机 Python 版本要求：>= 3.12（脚本负责检查，不负责自动安装）

## 核心行为

### 依赖与环境初始化

- 检查 Python：
  - macOS/Linux：`python3`
  - Windows：优先使用 `py -3`，否则回退 `python`
- 检查版本 >= 3.12，不满足则直接退出并提示
- 在项目根目录创建/复用 `.venv`：
  - `python -m venv .venv`
  - `.venv/bin/python -m pip install -r requirements.txt`（Windows 使用 `.venv\\Scripts\\python.exe`）
- 若 `.env` 不存在，自动从 `.env.example` 复制生成 `.env`

### 默认运行模式（保证“项目运行测试”可重复）

- 默认用离线 provider 运行一次（避免非交易时段卡住，避免 AkShare 网络波动）：  
  - `DATA_PROVIDER=offline`
  - `STRICT_TRADING_SESSIONS=false`
  - `MAX_LOOPS=1`
  - 将轮询间隔缩短为 1 秒，保证快速验证链路可跑通

### 可选切换

- 脚本支持参数 `--provider akshare`（或 PowerShell 参数 `-Provider akshare`）以运行真实 AkShare 行情（仍建议用户开盘时段运行）

## 文件变更

- 新增：`scripts/run.sh`
- 新增：`scripts/run.ps1`
- 修改：`.gitignore`（忽略 `.venv/`）
- 修改：`README.md`（增加“一键运行”说明）

