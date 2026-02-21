from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    WALLET_ADDRESS: str
    EOA_PRIVATE_KEY: str
    CLOB_API_KEY: str
    CLOB_API_SECRET: str
    CLOB_PASSPHRASE: str
    
    CHAIN_ID: int = 137
    POLYGON_RPC_URL: str = "https://polygon-rpc.com"
    
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

settings = Settings()
