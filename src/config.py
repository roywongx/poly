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
    
    POISON_KEYWORDS: List[str] = [
        'dispute', 'uma', 'opinion', 'oscars', 'twitter', 
        'tweet', 'x.com', 'announce', 'live', 'next goal', 'minute'
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
