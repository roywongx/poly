import asyncio
import json
import time
from loguru import logger
from typing import Dict

class RiskMonitor:
    def __init__(self, clob_client, execution_engine):
        self.client = clob_client
        self.execution = execution_engine
        self.active_positions = {}
        self.is_running = False

    async def watch_portfolio(self):
        self.is_running = True
        while self.is_running:
            try:
                async with self.client.connect_websocket() as ws:
                    await self._subscribe(ws)
                    async for message in ws:
                        data = json.loads(message)
                        await self._handle_message(data)
            except Exception as e:
                logger.error(f"WS Error: {e}")
                await asyncio.sleep(5)

    async def _subscribe(self, ws):
        auth_msg = self.client.create_ws_auth()
        await ws.send(json.dumps(auth_msg))
        subscribe_msg = {
            "type": "subscribe",
            "channels": ["user", "book_v2"],
            "token_ids": ["*"]
        }
        await ws.send(json.dumps(subscribe_msg))

    async def _handle_message(self, data: Dict):
        event_type = data.get("event_type")
        if event_type == "ORDER_UPDATE":
            payload = data.get("payload", {})
            if payload.get("status") == "FILLED":
                await self.execution.handle_order_fill(payload)
                self._add_to_monitoring(payload)
        elif event_type == "BOOK_UPDATE":
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

        best_bid = float(book_data.get("bids")[0][0]) if book_data.get("bids") else 0
        pos = self.active_positions[token_id]

        if best_bid < 0.90:
            await self._cancel_tp_orders(token_id)
            if best_bid < 0.89:
                if not pos["l2_trigger_time"]:
                    pos["l2_trigger_time"] = time.time()
                elif time.time() - pos["l2_trigger_time"] > 30:
                    await self._force_exit(token_id, "L2_STOP")
            else:
                pos["l2_trigger_time"] = None
        else:
            pos["l2_trigger_time"] = None

    async def _cancel_tp_orders(self, token_id: str):
        try:
            open_orders = await self.client.get_open_orders(token_id)
            for order in open_orders:
                if float(order['price']) == 0.99:
                    await self.client.cancel_order(order['order_id'])
        except: pass

    async def _force_exit(self, token_id: str, reason: str):
        try:
            balance_resp = await self.client.get_balance(token_id)
            balance = float(balance_resp.get("balance", 0))
            if balance > 0:
                order_args = self.execution.create_market_sell_order(token_id, balance)
                signed = self.client.create_order(order_args)
                await self.client.post_order(signed)
                self.active_positions.pop(token_id, None)
        except Exception as e:
            logger.critical(f"Exit Failed: {e}")
