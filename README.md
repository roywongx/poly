# 🗡️ PolyMarket Arena Bot V8.0 (Multi-Strategy Engine)

[English](#english) | [中文](#中文)

---

## 🌐 1-Click Web Dashboard / 零代码网页控制面板 (V8.0)

Forget about editing code or configuration files. V8.0 introduces a modern, bilingual Web Dashboard that allows you to control a fleet of bots from your browser.
忘掉枯燥的代码和配置文件吧。V8.0 引入了现代化的中英双语网页控制面板，一切操作都在浏览器中可视化完成，并能同时监控多个机器人的战斗。

**How to start / 如何启动:**
1. Open your terminal / 打开命令行终端.
2. Run the dashboard script / 运行面板服务:
   ```powershell
   python src/dashboard.py
   ```
3. Open your browser and go to / 打开浏览器访问: **`http://localhost:8000`**

### Features / 面板功能:
- **Arena Leaderboard (斗兽场排行榜)**: Watch Sniper, Trend, and Arb bots compete in real-time based on Win Rate and P&L.
- **Paper Trading Mode (无风险模拟盘)**: Test strategies safely without risking real USDC.
- **Live Trade History (实时交易流水)**: See exactly why a bot bought a market and its final outcome, powered by an underlying SQLite database.
- **Visual Configuration (可视化调参)**: Change bet size, risk limits, and safety filters on the fly.

---

<a name="english"></a>

## English

### 🛡️ Strategy & Safety Filters
To ensure safety, the engine comes pre-configured with industry-vetted safety filters that apply to ALL bots in the arena.

#### 🚫 Dangerous Categories
The following categories are excluded by default:
- **Sports**: Extremely high volatility and dominated by HFT (High-Frequency Trading) bots.
- **Pop Culture / Entertainment**: Often based on rumors or subjective interpretations.

#### 🧪 Poison Keywords
We skip any markets containing these "Poison" words:
- `UMA`, `Dispute`: Signals potential conflicts in settlement.
- `Twitter`, `X.com`, `Death`, `Rumor`, `Fake`: High misinformation risk.

### 🧠 Design Philosophy: The "Arena" Approach
V8.0 transitions from a single monolithic bot to a multi-bot architecture:
- **Sniper-V1**: The classic conservative bot. Needs >93% win probability.
- **Trend-V1**: A momentum follower. Enters at >70% if the market shows strong positive momentum.
- **Arb-V1**: The aggressive short-term arbitrage bot. Enters at >60% but demands massive 10x liquidity to ensure quick exits.
- **Learning Infrastructure**: Backed by `learning.py` and `db.py`, laying the foundation for Bayesian adaptive learning to automatically tweak these thresholds in V9.0.

### 🚀 Advanced Installation (CLI)

#### **Windows**
1. **Prepare Environment**:
   ```powershell
   cd PolyMarket-Arb-Bot-V6
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
2. **Onboarding (Wallet Setup)**:
   ```powershell
   python scripts/onboard_user.py
   ```

#### **Linux / macOS**
1. **Prepare Environment**:
   ```bash
   cd PolyMarket-Arb-Bot-V6
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Onboarding (Wallet Setup)**:
   ```bash
   python3 scripts/onboard_user.py
   ```

---

<a name="中文"></a>

## 中文

### 🛡️ 核心策略与安全过滤
为了确保资金安全，引擎预设了适用于所有机器人的全局安全过滤机制。

#### 🚫 危险分类 (Excluded Categories)
以下分类默认被排除：
- **Sports (体育)**: 极高的波动性，且充斥着高频交易机器人。
- **Pop Culture (流行文化) / 娱乐**: 结果往往基于主观判断或谣言。

#### 🧪 违禁词库 (Poison Keywords)
我们避开包含以下“毒药”词汇的市场：
- `UMA`, `Dispute`: 强烈暗示争议和仲裁。
- `Twitter`, `Rumor`, `Fake`: 假消息风险极高。

### 🧠 设计思想：“斗兽场”架构
V8.0 彻底重构了底层，从单一机器人进化为“多策略并行竞争”的斗兽场模式：
- **Sniper-V1 (狙击手)**: 维持严苛标准，胜率 > 93% 且流动性达标才出手。
- **Trend-V1 (趋势客)**: 门槛降至 70%，但要求标的有极强的上升动能。
- **Arb-V1 (套利者)**: 门槛降至 60%，激进打法，但要求 10 倍的超高深度护航。
- **成长型基因**: 引入了 SQLite 本地数据库和贝叶斯特征提取 (`learning.py`)，它会默默记录每一次输赢的特征，为未来的参数自动进化做准备。

### 🚀 命令行安装指南 (开发者)

#### **Windows 系统**
1. **环境准备**：
   ```powershell
   cd PolyMarket-Arb-Bot-V6
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
2. **凭证配置 (导入钱包)**：
   ```powershell
   python scripts/onboard_user.py
   ```

#### **Linux / macOS 系统**
1. **环境准备**：
   ```bash
   cd PolyMarket-Arb-Bot-V6
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

---

## ⚠️ Disclaimer / 免责声明
This software is for educational purposes. Trading involves risk. Never risk money you cannot afford to lose. Default runs in PAPER MODE.
本软件仅供技术研究，默认运行在无风险模拟盘。量化交易具有高度风险，请谨慎操作。