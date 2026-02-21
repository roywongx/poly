import asyncio
import json
import time
from datetime import datetime, timedelta
from loguru import logger
from typing import List, Dict
from .config import settings

class RiskMonitor:
    def __init__(self, clob_client, execution_engine):
        self.client = clob_client
        self.execution = execution_engine
        
        # 活跃持仓监控: {token_id: {"entry_price": float, "l2_start_time": float}}
        self.active_positions = {}
        self.is_running = False

        # 系统熔断记录: [timestamp1, timestamp2...]
        self.stop_loss_history: List[float] = []

    async def watch_portfolio(self):
        """
        全天候 24h 风控监控
        """
        self.is_running = True
        while self.is_running:
            try:
                # 检查熔断状态
                if await self._check_circuit_breaker():
                    await asyncio.sleep(60)
                    continue

                async with self.client.connect_websocket() as ws:
                    await self._subscribe(ws)
                    async for message in ws:
                        data = json.loads(message)
                        await self._handle_message(data)
            except Exception as e:
                logger.error(f"WS Reconnecting: {e}")
                await asyncio.sleep(5)

    async def _check_circuit_breaker(self) -> bool:
        """
        V7.0 系统级熔断：12h 内触发 2 次硬止损 -> 休眠 24h
        """
        now = time.time()
        # 仅保留最近 12 小时的止损记录
        cutoff = now - (settings.CB_WINDOW_HOURS * 3600)
        self.stop_loss_history = [ts for ts in self.stop_loss_history if ts > cutoff]
        
        if len(self.stop_loss_history) >= settings.CB_MAX_HARD_STOPS:
            logger.critical(f"GLOBAL CIRCUIT BREAKER TRIGGERED! Sleeping for {settings.CB_SLEEP_HOURS} hours.")
            # 这里的休眠会阻塞风控循环，实际上应该通知主程序暂停 Scanner
            # 简单实现：休眠 Monitor，并在日志中大写警示
            # 在生产环境中，建议抛出异常让 main.py 捕获并暂停整个 loop
            return True
        return False

    async def _handle_message(self, data: Dict):
        event_type = data.get("event_type")
        if event_type == "ORDER_UPDATE":
            payload = data.get("payload", {})
            if payload.get("status") == "FILLED":
                # 核心功能：秒级止盈 (Scalpel Mode)
                await self.execution.handle_order_fill(payload)
                self._add_to_monitoring(payload)

        elif event_type == "BOOK_UPDATE":
            # 核心功能：严苛止损 (Strict Stop-Loss)
            await self._check_stop_loss(data.get("payload"))

    def _add_to_monitoring(self, payload: Dict):
        token_id = payload.get("token_id")
        if token_id not in self.active_positions:
            self.active_positions[token_id] = {
                "entry_price": float(payload.get("price")),
                "l2_trigger_time": None
            }

    async def _check_stop_loss(self, book_data: Dict):
        token_id = book_data.get("token_id")
        if token_id not in self.active_positions: return

        # 获取当前最优买价
        best_bid = float(book_data.get("bids")[0][0]) if book_data.get("bids") else 0
        pos = self.active_positions[token_id]

        # L1: 预警线 (0.91) - 撤销止盈
        if best_bid < settings.STOP_LOSS_L1_TRIGGER:
            await self._cancel_tp_orders(token_id)
            
            # L2: 硬止损 (0.85) - 确认期 15s
            if best_bid < settings.STOP_LOSS_L2_TRIGGER:
                if not pos["l2_trigger_time"]:
                    pos["l2_trigger_time"] = time.time()
                    logger.warning(f"L2 TIMER STARTED for {token_id} (Bid: {best_bid})")
                elif time.time() - pos["l2_trigger_time"] > settings.STOP_LOSS_L2_CONFIRM_SECONDS:
                    # 触发硬止损，并记录熔断点
                    await self._force_exit(token_id, "L2_HARD_STOP")
                    self.stop_loss_history.append(time.time())
            else:
                pos["l2_trigger_time"] = None # 价格回升，重置计时器
        else:
            pos["l2_trigger_time"] = None

    async def _force_exit(self, token_id: str, reason: str):
        try:
            # 市价全平逻辑 (Taker Exit)
            balance_resp = await self.client.get_balance(token_id)
            balance = float(balance_resp.get("balance", 0))
            if balance > 0:
                logger.critical(f"EXECUTING HARD STOP: {token_id} | {reason}")
                order_args = self.execution.create_market_sell_order(token_id, balance)
                signed = self.client.create_order(order_args)
                await self.client.post_order(signed)
                
                self.active_positions.pop(token_id, None)
        except Exception as e:
            logger.critical(f"Exit Failed: {e}")
