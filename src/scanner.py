import asyncio
from datetime import datetime, timezone, timedelta
from loguru import logger
from typing import List, Dict, Optional
from .config import settings

class MarketScanner:
    def __init__(self, clob_client):
        self.client = clob_client

    async def get_eligible_markets(self) -> List[Dict]:
        """
        V7.0 极短线扫描逻辑：
        1. 过滤黑名单词汇
        2. 过滤黑名单分类 (Categories)
        3. 时间窗口：仅 1h - 12h
        4. 流动性深度 >= 5 * OrderAmount
        5. 动量趋势过滤：拒绝下跌趋势
        """
        logger.info("Scanning for Scalpel V7.0 opportunities...")
        try:
            # 假设 fetch_active_markets 返回了包含 endDate 的原始数据
            all_markets = await self.fetch_active_markets() 
            eligible = []
            
            logger.debug(f"Fetched {len(all_markets)} total active markets from API.")
            
            for market in all_markets:
                question = market.get('question', 'Unknown')
                
                # 0. 检查分类 (Category)
                category = market.get('category', '')
                excluded_cats = [c.strip().lower() for c in settings.EXCLUDED_CATEGORIES.split(',') if c.strip()]
                if category.lower() in excluded_cats:
                    logger.debug(f"[FILTERED] Category '{category}' is excluded: {question}")
                    continue

                # 1. 黑名单过滤
                if self._is_poisoned(market):
                    logger.debug(f"[FILTERED] Poison keyword found: {question}")
                    continue
                
                # 2. 极短线时间窗口过滤
                if not self._check_time_window(market):
                    logger.debug(f"[FILTERED] Outside time window: {question}")
                    continue
                
                # 3. 核心：流动性与动量趋势检查 (Risk Checks)
                if await self._check_safety_locks(market):
                    eligible.append(market)
                    logger.success(f"🎯 TARGET ACQUIRED: {question} | Category: {category} | Expiring soon!")
                else:
                    logger.debug(f"[FILTERED] Failed safety locks (Liquidity/Momentum): {question}")
            
            logger.info(f"Scan complete. Found {len(eligible)} eligible markets.")
            return eligible
        except Exception as e:
            logger.error(f"Scan failed: {e}")
            return []

    def _is_poisoned(self, market: Dict) -> bool:
        content = (market.get('question', '') + " " + market.get('description', '')).lower()
        keywords = [k.strip().lower() for k in settings.POISON_KEYWORDS.split(',') if k.strip()]
        for kw in keywords:
            if kw in content:
                return True
        return False

    def _check_time_window(self, market: Dict) -> bool:
        """
        V7.0 严苛时间窗口：仅允许 1h - 12h
        """
        try:
            end_time_str = market.get('end_date_iso')
            if not end_time_str: return False
            
            end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            hours_to_end = (end_time - now).total_seconds() / 3600

            # 必须在设定的极短线窗口内
            if settings.MIN_HOURS_TO_EXPIRY <= hours_to_end <= settings.MAX_HOURS_TO_EXPIRY:
                return True
            return False
        except Exception:
            return False

    async def _check_safety_locks(self, market: Dict) -> bool:
        """
        流动性锁 + 动量趋势过滤 (Momentum Filter)
        """
        token_id = market.get('condition_id') 
        try:
            # A. 流动性深度检查
            ob = await self.client.get_order_book(token_id)
            if not ob.bids: return False
            
            # 只需要前两档买单
            bids = ob.bids[:2]
            best_bid = float(bids[0].price)
            
            # 价格区间检查 (0.95 - 0.97)
            if not (settings.ENTRY_PRICE_MIN <= best_bid <= settings.ENTRY_PRICE_MAX):
                return False

            total_depth = sum(float(b.size) * float(b.price) for b in bids)
            if total_depth < (settings.ORDER_AMOUNT_USD * settings.LIQUIDITY_DEPTH_MULTIPLIER):
                return False

            # B. 动量趋势过滤 (Momentum Filter) - 拒绝接飞刀
            # 获取过去 2 小时的历史K线 (假设 interval="5m")
            # 注意：需确认 API 是否支持 history，若不支持可用 snapshot 估算
            history = await self.client.get_price_history(token_id, interval="5m") 
            
            # 只需要最近 2 小时的数据点 (24个点)
            recent_high = 0.0
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=settings.MOMENTUM_LOOKBACK_HOURS)
            
            # 简单的最高价提取逻辑
            recent_candles = [p for p in history if datetime.fromtimestamp(p['timestamp'], timezone.utc) > cutoff_time]
            if recent_candles:
                recent_high = max(float(p['max_price']) for p in recent_candles)
            
            # 核心判断：若过去2小时最高价 > 现价 + 0.02 -> 视为下跌趋势，拒绝
            if recent_high > (best_bid + settings.MAX_PRICE_DROP_TOLERANCE):
                logger.warning(f"Momentum Rejected: {token_id} (High: {recent_high} > Bid: {best_bid})")
                return False
                
            return True
        except Exception as e:
            logger.error(f"Safety check error: {e}")
            return False

    async def fetch_active_markets(self) -> List[Dict]:
        # Placeholder for actual API call
        return []
