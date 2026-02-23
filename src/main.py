import asyncio
import sys
import signal
from loguru import logger
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import ApiCreds

from .config import settings
from .scanner import MarketScanner
from .monitor import RiskMonitor
from . import db
from .bots.sniper_bot import SniperBot
from .bots.trend_bot import TrendBot
from .bots.arb_bot import ArbBot

import os
import requests

class PolyArbBot:
    def __init__(self):
        # 自动创建日志目录
        if not os.path.exists("logs"):
            os.makedirs("logs")
        
        # 记录日志到文件以便 Dashboard 读取
        import datetime
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        log_name = f"logs/bot_{timestamp}.log"
        
        # 移除默认 logger 并添加带强制刷新的 sink
        logger.remove() 
        logger.add(sys.stderr, level="INFO") # 保持控制台输出
        logger.add(log_name, rotation="10 MB", retention="7 days")
        
        # 建立指引文件，告诉 Dashboard 现在的日志路径
        try:
            with open("logs/LATEST", "w", encoding="utf-8") as f:
                f.write(log_name)
        except: pass
        
        logger.info(f"Engine Sparked. Tracking: {log_name}")
            
        host = "https://clob.polymarket.com"
        
        # 构造新版 SDK 所需的 ApiCreds 对象
        creds = ApiCreds(
            api_key=settings.CLOB_API_KEY,
            api_secret=settings.CLOB_API_SECRET,
            api_passphrase=settings.CLOB_PASSPHRASE
        )
        
        self.clob_client = ClobClient(
            host=host,
            key=settings.EOA_PRIVATE_KEY,
            chain_id=settings.CHAIN_ID,
            creds=creds,
            signature_type=int(settings.SIGNATURE_TYPE) if settings.SIGNATURE_TYPE else 0,
            funder=settings.FUNDER_ADDRESS if settings.FUNDER_ADDRESS else None
        )
        self.scanner = MarketScanner(self.clob_client)
        self.is_running = False
        
        # Initialize bots
        self.bots = [
            SniperBot(),
            TrendBot(),
            ArbBot()
        ]
        
        # Sync bots to DB and load custom params
        for bot in self.bots:
            db_config = db.get_bot_config(bot.name)
            if db_config:
                bot.params.update(db_config)
            else:
                db.save_bot_config(bot.name, bot.__class__.__name__, 1, bot.params)

    async def start(self):
        self.is_running = True
        logger.success(f"PolyMarket Arena Started in {'PAPER' if settings.PAPER_MODE else 'LIVE'} mode")
        tasks = [
            asyncio.create_task(self.scanner_loop())
        ]
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            pass
        finally:
            await self.shutdown()

    async def fetch_ob(self, token_id):
        try:
            url = f"https://clob.polymarket.com/book?token_id={token_id}"
            resp = await asyncio.get_event_loop().run_in_executor(None, requests.get, url)
            if resp.status_code == 200:
                data = resp.json()
                class MockBid:
                    def __init__(self, d):
                        self.price = d['price']
                        self.size = d['size']
                return [MockBid(b) for b in data.get('bids', [])]
            return []
        except Exception:
            return []

    async def scanner_loop(self):
        while self.is_running:
            try:
                markets = await self.scanner.get_eligible_markets()
                for market in markets:
                    token_id = market.get('token_id')
                    if not token_id: continue
                    
                    bids = await self.fetch_ob(token_id)
                    if not bids: continue
                    
                    for bot in self.bots:
                        signal = await bot.analyze(market, bids)
                        if signal.get("action") == "buy":
                            await bot.execute(market, signal, self.clob_client)
                            
                await asyncio.sleep(15) # Faster scanning loop like Arena
            except Exception as e:
                logger.error(f"Scanner loop error: {e}")
                await asyncio.sleep(10)

    async def shutdown(self):
        self.is_running = False
        logger.warning("Shutting down...")

if __name__ == "__main__":
    bot = PolyArbBot()
    try:
        asyncio.run(bot.start())
    except KeyboardInterrupt:
        pass
