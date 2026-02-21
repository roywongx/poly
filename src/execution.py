import asyncio
from loguru import logger
from typing import Dict, Optional
from py_clob_client.clob_types import OrderArgs, OrderType
from .config import settings

class ExecutionEngine:
    def __init__(self, clob_client):
        self.client = clob_client
        self.active_entry_orders = {}
        self.tp_placed_orders = set()

    async def process_signal(self, market: Dict, time_class: str):
        token_id = market.get('token_id')
        target_price = await self._calculate_sniping_price(token_id, time_class)
        if not target_price: return

        order_id = await self.place_maker_order(
            side="BUY", 
            size=settings.ORDER_AMOUNT_USD / target_price, 
            price=target_price, 
            token_id=token_id
        )

        if order_id:
            self.active_entry_orders[order_id] = {
                "token_id": token_id,
                "timestamp": asyncio.get_event_loop().time(),
                "market_name": market.get('question')
            }
            asyncio.create_task(self._monitor_order_timeout(order_id))

    async def _calculate_sniping_price(self, token_id: str, time_class: str) -> Optional[float]:
        try:
            ob = await self.client.get_order_book(token_id)
            if not ob.bids: return 0.94
            
            best_bid = float(ob.bids[0].price)
            sniping_price = best_bid + 0.001
            
            if time_class == "A":
                sniping_price = max(0.94, min(sniping_price, 0.96))
            elif time_class == "B":
                sniping_price = max(0.96, min(sniping_price, 0.97))
                
            return round(sniping_price, 3)
        except Exception as e:
            logger.error(f"Price calc error: {e}")
            return None

    def create_market_sell_order(self, token_id: str, size: float):
        return OrderArgs(
            price=0.1, 
            size=round(float(size), 2),
            side="SELL",
            token_id=token_id,
            order_type=OrderType.GTC
        )

    async def place_maker_order(self, side: str, size: float, price: float, token_id: str) -> Optional[str]:
        try:
            order_args = OrderArgs(
                price=float(price),
                size=round(float(size), 2),
                side=side,
                token_id=token_id,
                order_type=OrderType.GTC_POST_ONLY
            )
            signed_order = self.client.create_order(order_args)
            resp = await self.client.post_order(signed_order)
            
            if resp and resp.get("success"):
                return resp.get("orderID")
            return None
        except Exception as e:
            logger.error(f"Order placement failed: {e}")
            return None

    async def handle_order_fill(self, fill_data: Dict):
        order_id = fill_data.get('order_id')
        if order_id in self.active_entry_orders and order_id not in self.tp_placed_orders:
            order_info = self.active_entry_orders[order_id]
            tp_order_id = await self.place_maker_order(
                side="SELL",
                size=fill_data.get('size'),
                price=0.99,
                token_id=order_info['token_id']
            )
            if tp_order_id:
                self.tp_placed_orders.add(order_id)

    async def _monitor_order_timeout(self, order_id: str):
        await asyncio.sleep(15 * 60)
        if order_id in self.active_entry_orders and order_id not in self.tp_placed_orders:
            try:
                await self.client.cancel_order(order_id)
                self.active_entry_orders.pop(order_id, None)
            except: pass
