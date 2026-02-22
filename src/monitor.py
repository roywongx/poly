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
        全天候 24h 风控监控 (采用高频轮询替代不稳定的 Websocket)
        """
        self.is_running = True
        while self.is_running:
            try:
                # 检查熔断状态
                if await self._check_circuit_breaker():
                    await asyncio.sleep(60)
                    continue

                await self._poll_orders()
                await self._poll_active_positions()

            except Exception as e:
                logger.error(f"Monitor Polling Error: {e}")
            
            await asyncio.sleep(2)  # 每 2 秒轮询一次

    async def _poll_orders(self):
        active_orders = list(self.execution.active_entry_orders.keys())
        for order_id in active_orders:
            if order_id in self.execution.tp_placed_orders:
                continue
            
            try:
                # py_clob_client 0.34.6 中的 get_order 是同步方法
                order_info = self.client.get_order(order_id)
                status = order_info.get("status") if isinstance(order_info, dict) else getattr(order_info, "status", None)
                
                if status in ["MATCHED", "FILLED"]:
                    token_id = self.execution.active_entry_orders[order_id]["token_id"]
                    size = getattr(order_info, "original_size", getattr(order_info, "size", 0)) if not isinstance(order_info, dict) else order_info.get("original_size", order_info.get("size", 0))
                    price = getattr(order_info, "price", 0) if not isinstance(order_info, dict) else order_info.get("price", 0)
                    
                    fill_data = {
                        "order_id": order_id,
                        "size": float(size) if size else 0.0,
                        "price": float(price) if price else 0.0,
                        "token_id": token_id
                    }
                    await self.execution.handle_order_fill(fill_data)
                    self._add_to_monitoring(fill_data)
            except Exception as e:
                pass # 忽略网络偶发报错，避免日志轰炸
            
            await asyncio.sleep(0.1)  # 避免触发 API 限流

    async def _poll_active_positions(self):
        active_tokens = list(self.active_positions.keys())
        for token_id in active_tokens:
            try:
                ob = self.client.get_order_book(token_id)
                if ob and hasattr(ob, "bids") and ob.bids:
                    book_data = {
                        "token_id": token_id,
                        "bids": [[ob.bids[0].price, getattr(ob.bids[0], "size", 0)]]
                    }
                    await self._check_stop_loss(book_data)
            except Exception as e:
                pass
            
            await asyncio.sleep(0.1)

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

    async def _cancel_tp_orders(self, token_id: str):
        for order_id in list(self.execution.tp_placed_orders):
            try:
                # py_clob_client uses cancel()
                self.client.cancel(order_id)
                self.execution.tp_placed_orders.remove(order_id)
            except Exception as e:
                logger.warning(f"Error cancelling TP order: {e}")

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
