# PolyMarket Scalpel Bot V7.0 (HFT Resistant Edition)

这是一款专为 Polymarket 预测市场设计的**极短线尾端套利机器人**。系统采用 Python 3.10+ 异步架构，核心逻辑在于利用“手术刀”般的精准度捕捉高胜率（>0.94）的市场尾端机会，并配合严苛的动量过滤与阶梯止损机制。

---

## 🛡️ 精妙的安全策略设计 (Security by Design)

本项目在设计之初就将“私钥安全”视为最高优先级，采用了超越普通脚本的**三层安全防御体系**：

### 1. 物理隔离：零明文存储 (Zero Plain-Text Storage)
大多数开源脚本要求将私钥写在 `.env` 或 `.json` 文件中，这在电脑中毒或代码误提交时会导致资金瞬间归零。
- **方案**：本项目采用了 **System Keyring (Scheme B)** 方案。
- **实现**：私钥和 API 凭证在输入后，会被直接存入操作系统内核级的“加密保险箱”（如 Windows 凭据管理器、macOS Keychain 或 Linux Secret Service/D-Bus）。磁盘上没有任何包含私钥的明文文件。

### 2. 本地签名：非托管运行 (Non-Custodial Execution)
- **原理**：机器人利用 Polymarket 的 L1+L2 架构，所有的交易签名均在您的本地内存中完成。
- **安全**：私钥**永远不会**通过网络发送给服务器，更不会泄露给任何第三方。

---

## 一、 系统架构说明 (Architecture)

本系统采用解耦的异步非阻塞架构，确保在极端行情波动下依然保持秒级响应：

- **`src/config.py` (配置中心)**: 统一管理凭证读取、黑名单关键词及 V7.0 策略核心参数。
- **`src/scanner.py` (动量扫描器)**: 锁定 `1h - 12h` 窗口，配合动量过滤防止“接飞刀”。
- **`src/execution.py` (订单引擎)**: 强制 `Post-Only` Maker 模式，实现 Tick-Sniping 抢跑挂单。
- **`src/monitor.py` (风控心脏)**: WebSocket 实时监控，三级阶梯止损逻辑。
- **`src/main.py` (调度与熔断)**: 集成全局电路熔断器，12h 内 2 次硬损即自动休眠 24h。

---

## 二、 软件部署说明

### 1. 环境初始化

#### Windows 系统:
```powershell
# 进入项目目录并创建虚拟环境
python -m venv venv
.\venv\Scripts\Activate.ps1
# 安装依赖
pip install -r requirements.txt
```

#### Linux 系统 (Ubuntu/Debian):
```bash
# 安装系统依赖 (keyring 驱动)
sudo apt-get update
sudo apt-get install python3-dev libdbus-1-dev libsecret-1-dev
# 进入项目目录并创建虚拟环境
python3 -m venv venv
source venv/bin/activate
# 安装依赖
pip install -r requirements.txt
```

### 2. 安全与凭证配置 (核心安全步骤)
运行以下脚本，按照提示粘贴您的私钥。脚本将自动完成 L2 账户激活并将凭证加密存入系统保险箱：
```bash
python3 scripts/onboard_user.py
```

### 3. 启动机器人
```bash
# 确保在虚拟环境下运行
python3 -m src.main
```

---

## 三、 V7.0 核心策略逻辑

| 维度 | 策略规则 | 目的 |
| :--- | :--- | :--- |
| **准入窗口** | 1小时 < 剩余时间 < 12小时 | 避开长线变数，锁定胜负已分的尾端 |
| **价格区间** | 0.94 - 0.99 | 激进捕获高概率确定性事件 |
| **进场方式** | Post-Only Limit Order (+0.001) | 确保始终是 Maker，杜绝 Taker 手续费 |
| **系统熔断** | 12h 内 2 次硬损即休眠 24h | 保护本金，避开系统性抛售潮 |

---

## 四、 运行维护建议

1. **安全性自检**: 本系统已默认通过 Keyring 加密存储。请勿为了图方便将私钥硬编码回代码。
2. **资金准备**: 钱包需保留少量 MATIC (Gas) 和足额 USDC (本金)。
3. **长期运行 (Linux)**: 建议在 Linux 服务器上使用 `screen` 或 `tmux` 运行机器人，以保持后台常驻。

---

**⚠️ 免责声明**: 本软件仅供量化交易技术研究参考。加密货币交易具有极高风险，请在自身风险承受能力范围内谨慎操作。
