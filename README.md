# 🗡️ PolyMarket Scalpel Bot V7.0 (HFT Resistant)

[English](#english) | [中文](#中文)

---

<a name="english"></a>

## English

### 🧠 Design Philosophy: The "Scalpel" Approach
PolyMarket Scalpel is a high-frequency-ready (HFT) short-term arbitrage bot. 
- **Precision**: Targets high-probability (0.94-0.99) outcomes in the final 1-12 hours.
- **Resilience**: Uses momentum filters to avoid "falling knives" and liquidity checks to prevent HFT front-running.
- **Security**: Private keys are stored in the OS-level hardware-backed keyring (AES-256), never in plain text.

### 🛡️ Feature Set
1.  **Security**: System Keyring (Scheme B) encryption.
2.  **Strategy**: 0.94+ "Sure Thing" logic with 5x liquidity depth requirement.
3.  **Risk Management**: L2 Hard Stop (0.85 price floor) and Global Circuit Breaker (24h sleep after 2 hard stops).

### 🚀 Detailed Installation

#### **Windows**
1. **Prepare Environment**:
   ```powershell
   cd PolyMarket-Arb-Bot-V6
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
2. **Onboarding**:
   ```powershell
   python scripts/onboard_user.py
   ```

#### **Linux (Ubuntu/Debian)**
1. **Install Dependencies**:
   ```bash
   sudo apt update && sudo apt install -y libdbus-1-dev libsecret-1-dev python3-dev
   ```
2. **Prepare Environment**:
   ```bash
   cd PolyMarket-Arb-Bot-V6
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. **Onboarding**:
   ```bash
   python3 scripts/onboard_user.py
   ```

#### **macOS**
1. **Prepare Environment**:
   ```bash
   cd PolyMarket-Arb-Bot-V6
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Onboarding**:
   ```bash
   python3 scripts/onboard_user.py
   ```

### ⚙️ Usage
- **Start Bot**: `python -m src.main`
- **Stop Bot**: Press `Ctrl + C` (Graceful shutdown).

---

<a name="中文"></a>

## 中文

### 🧠 设计思想：“手术刀”原则
PolyMarket Scalpel 是一款专为极短线套利设计的机器人。
- **精准度**：仅锁定距离结算前 1-12 小时、胜率极高（价格 0.94-0.99）的市场。
- **抗 HFT**：通过动量过滤拒绝“接飞刀”，通过流动性倍率检查防止被高频机器人围猎。
- **安全性**：私钥存储于操作系统内核级加密保险箱（AES-256），永不以明文形式存在于磁盘。

### 🛡️ 功能特性
1.  **安全架构**：采用 System Keyring (Scheme B) 加密方案。
2.  **核心策略**：0.94+ 稳赢逻辑，要求订单簿深度至少为交易额的 5 倍。
3.  **风控系统**：L2 硬止损（价格跌破 0.85 持续 15s 强制平仓）及全局熔断机制。

### 🚀 详细安装指南

#### **Windows 系统**
1. **环境准备**：
   ```powershell
   cd PolyMarket-Arb-Bot-V6
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
2. **凭证配置**：
   ```powershell
   python scripts/onboard_user.py
   ```

#### **Linux 系统 (Ubuntu/Debian)**
1. **安装系统依赖**：
   ```bash
   sudo apt update && sudo apt install -y libdbus-1-dev libsecret-1-dev python3-dev
   ```
2. **环境准备**：
   ```bash
   cd PolyMarket-Arb-Bot-V6
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. **凭证配置**：
   ```bash
   python3 scripts/onboard_user.py
   ```

#### **macOS 系统**
1. **环境准备**：
   ```bash
   cd PolyMarket-Arb-Bot-V6
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. **凭证配置**：
   ```bash
   python3 scripts/onboard_user.py
   ```

### ⚙️ 运行说明
- **启动机器人**：`python -m src.main`
- **停止机器人**：按下 `Ctrl + C`（程序将安全撤单并退出）。

---

## ⚠️ Disclaimer / 免责声明
This software is for educational purposes. Trading involves risk. 
本软件仅供技术研究，量化交易具有高度风险，请谨慎操作。
