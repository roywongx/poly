import keyring
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, model_validator
from typing import List, Optional

class Settings(BaseSettings):
    # 非敏感配置可以继续留在 .env 或默认值
    WALLET_ADDRESS: str
    CHAIN_ID: int = 137
    POLYGON_RPC_URL: str = "https://polygon-rpc.com"
    
    # 敏感字段设为 Optional，我们将通过 validator 从 keyring 填充
    EOA_PRIVATE_KEY: Optional[str] = None
    CLOB_API_KEY: Optional[str] = None
    CLOB_API_SECRET: Optional[str] = None
    CLOB_PASSPHRASE: Optional[str] = None
    
    ORDER_AMOUNT_USD: float = 50.0
    MAX_ACTIVE_POSITIONS_PER_CATEGORY: int = 5
    GLOBAL_MAX_POSITIONS: int = 10
    
    # V7.0 策略核心参数
    # 时间窗口：仅允许 1h - 12h
    MIN_HOURS_TO_EXPIRY: float = 1.0
    MAX_HOURS_TO_EXPIRY: float = 12.0
    
    # 进场价格区间 (V7.0 激进版：0.94 - 0.99)
    ENTRY_PRICE_MIN: float = 0.94
    ENTRY_PRICE_MAX: float = 0.99
    
    # 动量过滤：拒绝接飞刀 (过去2小时高点 - 现价 > 0.02)
    MOMENTUM_LOOKBACK_HOURS: int = 2
    MAX_PRICE_DROP_TOLERANCE: float = 0.02

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
        keys = ["EOA_PRIVATE_KEY", "CLOB_API_KEY", "CLOB_API_SECRET", "CLOB_PASSPHRASE"]
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
