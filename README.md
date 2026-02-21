# PolyMarket Scalpel Bot V7.0 (HFT Resistant Edition)

这是一款专为 Polymarket 预测市场设计的**极短线尾端套利机器人**。系统采用 Python 3.10+ 异步架构，核心逻辑在于利用“手术刀”般的精准度捕捉高胜率（>0.94）的市场尾端机会。

---

## 🛡️ 安全设计 (Security)

本项目采用了 **System Keyring (Scheme B)** 加密方案：
- **物理隔离**：私钥不存储于任何文本文件中，而是存入操作系统内核级的加密保险箱。
- **本地签名**：所有交易均在本地内存完成签名，私钥永不联网。

---

## 🚀 快速部署 (Deployment)

### 1. 环境准备

| 操作系统 | 激活指令 | 依赖安装 |
| :--- | :--- | :--- |
| **Windows** | `.\venv\Scripts\Activate.ps1` | `pip install -r requirements.txt` |
| **Linux** | `source venv/bin/activate` | `sudo apt install libdbus-1-dev libsecret-1-dev && pip install -r requirements.txt` |

### 2. 凭证配置 (核心)
运行以下脚本，按照提示粘贴您的私钥。脚本将自动完成 L2 账户激活并将凭证安全存储：
```bash
# 推荐使用 python3
python3 scripts/onboard_user.py
```

### 3. 启动机器人
```bash
python3 -m src.main
```

---

## 📈 策略概览 (Strategy V7.0)

- **入场区间**：价格在 `0.94 - 0.99` 之间。
- **时间窗口**：仅锁定距离结算前 `1h - 12h` 的快消型市场。
- **动量过滤**：排除过去 2h 跌幅超过 `$0.02` 的飞刀标的。
- **严苛止损**：现价跌破 `0.85` 并持续 15 秒即全仓 Taker 平仓。
- **全局熔断**：12h 内触发 2 次硬损即自动休眠 24h。

---

## ❓ 常见问题 (FAQ)

**Q: 为什么运行提示 ModuleNotFoundError?**
A: 请确保您已激活虚拟环境 `(venv)` 并运行了 `pip install -r requirements.txt`。

**Q: 为什么注册提示 400 错误?**
A: 您的钱包需要至少 0.1 MATIC，并建议先在官网手动完成一次 "Enable Trading" 签名。

**Q: 如何修改交易金额?**
A: 在根目录创建 `.env` 文件，设置 `ORDER_AMOUNT_USD=10` 即可。

---

**⚠️ 免责声明**: 本软件仅供量化交易技术研究。加密货币交易具有高风险，请谨慎操作。
