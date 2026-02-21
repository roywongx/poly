import asyncio
from datetime import datetime, timezone
from loguru import logger
from typing import List, Dict, Optional
from .config import settings

class MarketScanner:
    def __init__(self, clob_client):
        self.client = clob_client

    async def get_eligible_markets(self) -> List[Dict]:
        logger.info("Starting market scan...")
        try:
            all_markets = await self.fetch_active_markets() 
            eligible = []
            for market in all_markets:
                if self._is_poisoned(market):
                    continue
                
                time_class = self._classify_by_time(market)
                if not time_class:
                    continue
                
                if await self._check_safety_locks(market, time_class):
                    market['time_class'] = time_class
                    eligible.append(market)
                    logger.success(f"Found eligible market: {market.get('question')} | Class: {time_class}")
            
            return eligible
        except Exception as e:
            logger.error(f"Scan failed: {e}")
            return []

    def _is_poisoned(self, market: Dict) -> bool:
        content = (market.get('question', '') + " " + market.get('description', '')).lower()
        for kw in settings.POISON_KEYWORDS:
            if kw in content:
                return True
        return False

    def _classify_by_time(self, market: Dict) -> Optional[str]:
        try:
            end_time_str = market.get('end_date_iso')
            if not end_time_str: return None
            
            end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            hours_to_end = (end_time - now).total_seconds() / 3600

            if 1 <= hours_to_end <= 12:
                return "A"
            elif 12 < hours_to_end <= 48:
                return "B"
            return None
        except Exception:
            return None

    async def _check_safety_locks(self, market: Dict, time_class: str) -> bool:
        token_id = market.get('condition_id') 
        try:
            ob = await self.client.get_order_book(token_id)
            if not ob.bids: return False
            
            bids = ob.bids[:2]
            total_depth = sum(float(b.size) * float(b.price) for b in bids)
            
            if total_depth < (settings.ORDER_AMOUNT_USD * settings.LIQUIDITY_DEPTH_MULTIPLIER):
                return False
                
            return True
        except Exception as e:
            logger.error(f"Safety check error: {e}")
            return False

    async def fetch_active_markets(self) -> List[Dict]:
        # TODO: Implement actual API call
        return []
