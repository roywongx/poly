from abc import ABC, abstractmethod
import asyncio
from loguru import logger
import uuid
from typing import Dict, Any

from src.config import settings
from src import db

class BaseBot(ABC):
    def __init__(self, name: str, params: dict):
        self.name = name
        self.params = params
        self.active_positions = {}

    @abstractmethod
    async def analyze(self, market: Dict, ob_bids: list) -> Dict[str, Any]:
        """
        Analyze a market and return a signal.
        Expected return format:
        {
            "action": "buy" | "skip",
            "confidence": float,
            "target_price": float,
            "reasoning": str
        }
        """
        pass

    async def execute(self, market: Dict, signal: Dict, clob_client):
        """Execute the trade based on PAPER_MODE."""
        token_id = market.get('token_id')
        target_price = signal.get("target_price")
        if not target_price: return

        amount_usd = settings.ORDER_AMOUNT_USD
        size = amount_usd / target_price
        
        mode = "paper" if settings.PAPER_MODE else "live"
        venue = "simulated" if settings.PAPER_MODE else "polymarket"
        
        if settings.PAPER_MODE:
            # Simulate instant fill
            order_id = f"paper_{uuid.uuid4().hex[:8]}"
            logger.info(f"[{self.name}] PAPER TRADE: Bought {size:.2f} shares of {market.get('question')[:30]} at {target_price:.3f}")
            
            # Log to DB
            trade_id = db.log_trade(
                bot_name=self.name,
                market_id=token_id,
                market_question=market.get('question'),
                side="yes", # Scanner already extracted YES/NO tokens and prefixed question
                amount=amount_usd,
                entry_price=target_price,
                shares_bought=size,
                confidence=signal.get("confidence", 0.0),
                reasoning=signal.get("reasoning", ""),
                features={"mom": market.get("oneDayPriceChange")},
                venue=venue,
                mode=mode
            )
            self.active_positions[trade_id] = {
                "token_id": token_id,
                "entry_price": target_price,
                "shares": size,
                "market": market.get('question')
            }
        else:
            # LIVE execution via CLOB
            from py_clob_client.clob_types import OrderArgs, OrderType
            try:
                order_args = OrderArgs(
                    price=target_price,
                    size=round(size, 2),
                    side="BUY",
                    token_id=token_id,
                    order_type=OrderType.GTC
                )
                signed_order = clob_client.create_order(order_args)
                resp = await clob_client.post_order(signed_order)
                
                if resp and resp.get("success"):
                    order_id = resp.get("orderID")
                    logger.success(f"[{self.name}] LIVE TRADE PLACED: {order_id}")
                    db.log_trade(
                        bot_name=self.name,
                        market_id=token_id,
                        market_question=market.get('question'),
                        side="yes",
                        amount=amount_usd,
                        entry_price=target_price,
                        shares_bought=size, # Assuming fully filled for simplicity in this demo
                        confidence=signal.get("confidence", 0.0),
                        reasoning=signal.get("reasoning", ""),
                        features={"mom": market.get("oneDayPriceChange")},
                        venue=venue,
                        mode=mode
                    )
            except Exception as e:
                logger.error(f"[{self.name}] Order placement failed: {e}")
