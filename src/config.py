import keyring
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, model_validator
from typing import List, Optional

class Settings(BaseSettings):
    # === 基础连接配置 ===
    WALLET_ADDRESS: str                                    # 您的钱包地址 (用于查询余额)
    CHAIN_ID: int = 137                                    # 网络 ID (Polygon 为 137)
    POLYGON_RPC_URL: str = "https://polygon-rpc.com"      # RPC 节点地址

    # === 核心交易参数 (Roy 的手术刀) ===
    ORDER_AMOUNT_USD: float = 50.0                         # 单次下注金额 (单位: USDC)。建议设置为总资金的 1%-5%。
    MAX_ACTIVE_POSITIONS_PER_CATEGORY: int = 5             # 同一类别的最大持仓数 (例如：政治话题最多同时买5单)，防止风险过度集中。
    GLOBAL_MAX_POSITIONS: int = 10                         # 全局最大持仓总数 (整个机器人同时运行的最大交易总单数)。

    # === V7.0 策略过滤参数 ===
    MIN_HOURS_TO_EXPIRY: float = 1.0                       # 最小剩余时间 (小时)，低于此时间不进场
    MAX_HOURS_TO_EXPIRY: float = 12.0                      # 最大剩余时间 (小时)，只做即将结算的单子
    ENTRY_PRICE_MIN: float = 0.94                          # 进场价格下限 (胜率 > 94%)
    ENTRY_PRICE_MAX: float = 0.99                          # 进场价格上限

    # === 动量与安全检查 ===
    MOMENTUM_LOOKBACK_HOURS: int = 2                       # 动量回溯时间 (2小时)
    MAX_PRICE_DROP_TOLERANCE: float = 0.02                 # 最大跌幅容忍度 (防止接飞刀)
    LIQUIDITY_DEPTH_MULTIPLIER: int = 5                    # 流动性要求 (订单簿深度必须是下注额的 X 倍)

    # === 敏感信息 (将从系统 Keyring 获取) ===
    EOA_PRIVATE_KEY: Optional[str] = None
    CLOB_API_KEY: Optional[str] = None
    CLOB_API_SECRET: Optional[str] = None
    CLOB_PASSPHRASE: Optional[str] = None
    FUNDER_ADDRESS: Optional[str] = None
    SIGNATURE_TYPE: Optional[str] = "0"

    # 严苛止损参数
    STOP_LOSS_L1_TRIGGER: float = 0.91 # 撤销止盈
    STOP_LOSS_L2_TRIGGER: float = 0.85 # 市价止损
    STOP_LOSS_L2_CONFIRM_SECONDS: int = 15
    
    # 系统级熔断 (Global Circuit Breaker)
    CB_WINDOW_HOURS: int = 12
    CB_MAX_HARD_STOPS: int = 2
    CB_SLEEP_HOURS: int = 24

    POISON_KEYWORDS: List[str] = [
        'dispute', 'uma', 'opinion', 'oscars', 'twitter', 
        'tweet', 'x.com', 'announce', 'live', 'next goal', 'minute',
        'tom hanks', 'ellen degeneres', 'rumor', 'death', 'fake'
    ]
    
    MAX_VOLATILITY_THRESHOLD: float = 0.05
    LIQUIDITY_DEPTH_MULTIPLIER: int = 5

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode='after')
    def load_secrets_from_keyring(self) -> 'Settings':
        service_id = "polymarket_bot"
        
        # 尝试从 Keyring 加载敏感信息
        keys = ["EOA_PRIVATE_KEY", "CLOB_API_KEY", "CLOB_API_SECRET", "CLOB_PASSPHRASE", "FUNDER_ADDRESS", "SIGNATURE_TYPE"]
        for key in keys:
            # 如果当前值为空（未在环境变量中设置），则从 keyring 获取
            if not getattr(self, key):
                val = keyring.get_password(service_id, key)
                if val:
                    setattr(self, key, val)
                else:
                    if key == "EOA_PRIVATE_KEY": # 私钥是强制要求的
                        raise ValueError(f"Missing critical secret: {key}. Please run scripts/setup_secrets.py")
        return self

settings = Settings()
