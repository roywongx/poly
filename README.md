# 🗡️ PolyMarket Scalpel Bot V7.0 (HFT Resistant)

[English](#english) | [中文](#中文)

---

## 🛡️ Strategy & Safety / 核心策略与安全 (V7.0)

To ensure the highest win rate (94%+), the bot comes pre-configured with industry-vetted safety filters.
为了确保极高的胜率（>94%），机器人预设了经过实战验证的安全过滤机制。

### 🚫 Dangerous Categories / 危险分类
The following categories are excluded by default because they are prone to high volatility, manipulation, or resolution disputes:
以下分类默认被排除，因为它们极易受到高波动、人为操纵或结算争议的影响：
- **Sports (体育)**: Extremely high volatility and dominated by HFT (High-Frequency Trading) bots.
- **Pop Culture (流行文化)**: Often based on rumors or subjective interpretations.
- **Entertainment (娱乐)**: Similar risks to pop culture, high dependency on "unreliable" social media sources.

### 🧪 Poison Keywords / 违禁词库
We skip any markets containing these "Poison" words to avoid ambiguity and resolution conflicts:
我们避开包含以下“毒药”词汇的市场，以防止结算歧义和争议：
- `UMA`, `Dispute`: Signals potential conflicts in how the market will be settled.
- `Twitter`, `X.com`: Sources that are too volatile or prone to fake news.
- `Announce`, `Live`, `Minute`: Real-time event risks where prices move faster than the bot can react.
- `Opinion`, `Subjective`: Markets that aren't based on hard, objective facts.
- `Death`, `Rumor`, `Fake`: High misinformation risk.

---

## 🌐 Web Dashboard / 网页控制面板 (New)

We have added a modern Web UI to monitor and control your bot in real-time.
我们增加了一个现代化的网页控制面板，用于实时监控和控制您的机器人。

**How to start the dashboard / 如何启动面板:**
```powershell
python src/dashboard.py
```
Then open your browser and go to / 然后打开浏览器访问: `http://localhost:8000`

---

## 🛠️ 管理控制台 / Management Console (New in V7.0)

We have introduced a beginner-friendly management script: `manage.py`.
You can use it to visually modify parameters, update the bot, and sync with GitHub safely.

⚠️ **Important:** Before running `manage.py` or the bot for the very first time, you MUST run the onboarding script to generate your `.env` configuration file:
```powershell
python scripts/onboard_user.py
```

**How to start the console:**
```powershell
python manage.py
```

---

## ⚙️ 参数配置 / Configuration

### 中文 (Chinese)
所有的核心参数都可以在根目录的 `.env` 文件中修改。强烈建议您使用上方的 `python manage.py` 命令进入**可视化管理控制台**进行修改，无需触碰代码。

⚠️ **注意：** 在首次运行 `manage.py` 或启动机器人之前，您**必须**先运行一次初始化向导来生成 `.env` 配置文件：
```powershell
python scripts/onboard_user.py
```

| 参数名称 | 白话文说明 | 建议设置 |
| :--- | :--- | :--- |
| **`ORDER_AMOUNT_USD`** | **单笔投资额**：机器人看准一个机会后，每次投入购买的 USDC (美元稳定币) 数量。 | 建议为您总资金的 **1% 到 5%**。例如总资金 $1000，可设为 $20-$50。 |
| **`GLOBAL_MAX_POSITIONS`** | **全盘最大持仓数**：机器人最多同时进行多少笔交易。达到这个数字后，机器人将暂停寻找新机会，直到现有订单结算。 | 建议设为 **10 到 20**。这决定了您最多占用多少总资金。 |
| **`MAX_ACTIVE_POSITIONS_PER_CATEGORY`** | **单话题最大持仓数**：为了防止资金过度集中在一个事件（如：大选、特定体育赛事）上翻车。 | 建议设为 **5**。这意味着对于同一个话题，机器人最多只会下 5 单。 |
| **`ENTRY_PRICE_MIN`** | **进场胜率底线**：在 Polymarket，价格即代表市场认为的胜率。0.94 代表只有当市场认为某事有 >94% 的概率发生时，我们才买入。 | 建议保持 **0.94**。V7.0 主打“稳赢”极高胜率策略。 |
| **`MAX_HOURS_TO_EXPIRY`** | **最长等待时间**：只扫描距离揭晓结果还有 X 小时内的市场。 | 建议保持 **12.0**。时间越短，确定性越高，资金周转越快。 |

### English
All core parameters can be safely modified using the interactive console: `python manage.py`. This is highly recommended over manually editing the `.env` file.

| Parameter | Beginner-Friendly Description | Recommended |
| :--- | :--- | :--- |
| **`ORDER_AMOUNT_USD`** | **Order Size**: The exact amount of USDC the bot will spend each time it finds a highly probable winning trade. | **1% - 5%** of your total bankroll. (e.g., $20-$50 for a $1000 account). |
| **`GLOBAL_MAX_POSITIONS`** | **Max Concurrent Trades**: The absolute maximum number of active bets the bot will hold at any one time across all topics. | **10 - 20**. Once reached, the bot stops buying until a trade resolves. |
| **`MAX_ACTIVE_POSITIONS_PER_CATEGORY`** | **Category Limit**: Prevents the bot from placing all your funds on variations of the same event (e.g., all bets on politics). | **5**. This means a maximum of 5 concurrent bets on a single topic. |
| **`ENTRY_PRICE_MIN`** | **Minimum Win Probability**: In Polymarket, price = probability. 0.94 means we only bet if the market believes there's a >94% chance of winning. | **0.94**. V7.0 focuses exclusively on extreme high-probability "sure things." |
| **`MAX_HOURS_TO_EXPIRY`** | **Max Wait Time**: Only scan and bet on markets that will resolve and pay out within this many hours. | **12.0**. Shorter timeframes mean faster capital turnover and higher certainty. |

---

<a name="english"></a>

## English

### 🧠 Design Philosophy: The "Scalpel" Approach
PolyMarket Scalpel is a high-frequency-ready (HFT) short-term arbitrage bot. 
- **Precision**: Targets extreme high-probability (0.94-0.99) outcomes in their final 1-12 hours.
- **Resilience**: Uses momentum filters to avoid "falling knives" and 5x liquidity checks to prevent HFT front-running and slippage.
- **Security First**: Private keys are heavily encrypted and stored in your operating system's hardware-backed keyring (AES-256). They never exist in plain text in the codebase.

### 🛡️ Feature Set
1.  **Bank-Grade Security**: OS System Keyring (Scheme B) encryption for wallets.
2.  **Ironclad Strategy**: 0.94+ "Sure Thing" logic demanding deep order book liquidity.
3.  **Risk Management Engine**: Includes L2 Hard Stops (panic sells if price crashes below 0.85) and a Global Circuit Breaker (halts trading for 24h if multiple stops are hit).

### 🚀 Detailed Installation

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

### ⚙️ Usage
- **Start Bot**: `python -m src.main`
- **Manage Settings**: `python manage.py` (Interactive console)
- **Stop Bot**: Press `Ctrl + C` (Performs a graceful shutdown, canceling open orders).

---

<a name="中文"></a>

## 中文

### 🧠 设计思想：“手术刀”原则
PolyMarket Scalpel 是一款专为极短线套利、追求极高胜率设计的机器人。
- **极致精准**：仅锁定距离揭晓结果前 1-12 小时、市场公认胜率极高（价格 0.94-0.99）的机会。
- **抗高频猎杀**：内置动量过滤拒绝“接飞刀”，并强制要求订单簿深度至少为下注额的 5 倍，防止滑点和高频机器人割韭菜。
- **军事级安全**：您的私钥被加密存储于 Windows/macOS 操作系统内核级的保险箱中，永不会以明文形式出现在代码或磁盘里。

### 🛡️ 功能特性
1.  **安全架构**：彻底摒弃 `.env` 明文存私钥，采用 System Keyring 硬件加密方案。
2.  **核心策略**：0.94+ 稳赢逻辑，资金安全第一，收益第二。
3.  **智能风控系统**：L2 级硬止损（若事件突发黑天鹅跌破 0.85 持续 15s 则强制割肉）及全局熔断机制（连续止损两次则罢工 24 小时保护本金）。

### 🚀 详细安装指南

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
2. **凭证配置 (导入钱包)**：
   ```bash
   python3 scripts/onboard_user.py
   ```

### ⚙️ 运行说明
- **启动机器人**：`python -m src.main`
- **打开管理控制台 (调参/更新)**：`python manage.py`
- **安全停止机器人**：在运行窗口按下 `Ctrl + C`（程序将自动撤销所有未成交的挂单并安全退出）。

---

## ⚠️ Disclaimer / 免责声明
This software is for educational purposes. Trading involves risk. Never risk money you cannot afford to lose.
本软件仅供技术研究，量化交易具有高度风险，任何参数设置都无法保证 100% 盈利。请谨慎操作，切勿投入无法承受损失的资金。
