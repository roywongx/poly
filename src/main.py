import asyncio
import sys
import signal
from loguru import logger
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import ApiCreds

from .config import settings
from .scanner import MarketScanner
from .execution import ExecutionEngine
from .monitor import RiskMonitor

import os

class PolyArbBot:
    def __init__(self):
        # 自动创建日志目录
        if not os.path.exists("logs"):
            os.makedirs("logs")
        
        # 记录日志到文件以便 Dashboard 读取
        logger.add("logs/bot_{time}.log", rotation="10 MB", retention="7 days")
            
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
        self.execution = ExecutionEngine(self.clob_client)
        self.scanner = MarketScanner(self.clob_client)
        self.monitor = RiskMonitor(self.clob_client, self.execution)
        self.is_running = False
        self.category_counts = {}

    async def start(self):
        self.is_running = True
        logger.success("PolyMarket Arb Bot Started")
        tasks = [
            asyncio.create_task(self.scanner_loop()),
            asyncio.create_task(self.monitor.watch_portfolio()),
            asyncio.create_task(self.state_dumper_loop())
        ]
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            pass
        finally:
            await self.shutdown()

    async def state_dumper_loop(self):
        import json
        while self.is_running:
            try:
                state = {
                    "active_entry_orders": self.execution.active_entry_orders,
                    "tp_placed_orders": list(self.execution.tp_placed_orders),
                    "active_positions": self.monitor.active_positions,
                    "category_counts": self.category_counts
                }
                with open("bot_state.json", "w", encoding="utf-8") as f:
                    json.dump(state, f, ensure_ascii=False, indent=2)
            except Exception as e:
                pass
            await asyncio.sleep(5)

    async def scanner_loop(self):
        while self.is_running:
            try:
                markets = await self.scanner.get_eligible_markets()
                for m in markets:
                    await self.execution.process_signal(m, m['time_class'])
                await asyncio.sleep(60)
            except Exception as e:
                logger.error(f"Scanner error: {e}")
                await asyncio.sleep(10)

    async def shutdown(self):
        self.is_running = False
        logger.warning("Shutting down...")
        for order_id in list(self.execution.active_entry_orders.keys()):
            try:
                await self.clob_client.cancel_order(order_id)
            except: pass

if __name__ == "__main__":
    bot = PolyArbBot()
    try:
        asyncio.run(bot.start())
    except KeyboardInterrupt:
        pass
