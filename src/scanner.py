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
            all_markets = await self.fetch_active_markets() 
            eligible = []
            
            stats = {
                "total": len(all_markets),
                "filtered_category": 0,
                "filtered_poison": 0,
                "filtered_time": 0,
                "filtered_safety": 0
            }
            
            logger.debug(f"Fetched {stats['total']} total active markets from API.")
            
            for market in all_markets:
                question = market.get('question', 'Unknown')
                
                # 0. 检查分类 (Category & Tags)
                category = market.get('category') or ""
                tags = [t.get('label', '') for t in market.get('tags', [])] if isinstance(market.get('tags'), list) else []
                combined_cat_info = (category + " " + " ".join(tags) + " " + market.get('question', '')).lower()
                
                excluded_cats = [c.strip().lower() for c in settings.EXCLUDED_CATEGORIES.split(',') if c.strip()]
                is_excluded = False
                for ec in excluded_cats:
                    if ec in combined_cat_info:
                        logger.debug(f"SKIP [Category:{ec}] {question[:50]}...")
                        stats["filtered_category"] += 1
                        is_excluded = True
                        break
                if is_excluded: continue

                # 1. 黑名单过滤
                if self._is_poisoned(market):
                    logger.debug(f"SKIP [Poison] {question[:50]}...")
                    stats["filtered_poison"] += 1
                    continue
                
                # 2. 极短线时间窗口过滤
                if not self._check_time_window(market):
                    logger.debug(f"SKIP [Time] {question[:50]}...")
                    stats["filtered_time"] += 1
                    continue
                
                # 3. 核心：流动性与动量趋势检查 (Risk Checks)
                if await self._check_safety_locks(market):
                    eligible.append(market)
                    logger.success(f"🎯 TARGET: {question}")
                else:
                    logger.debug(f"SKIP [Safety] {question[:50]}...")
                    stats["filtered_safety"] += 1
            
            summary = (
                f"Scan Complete! {len(eligible)} Found.\n"
                f"  Summary ({stats['total']} analyzed):\n"
                f"  🚫 {stats['filtered_category']} Cat | ☠️ {stats['filtered_poison']} Poison | ⏳ {stats['filtered_time']} Time | 🛡️ {stats['filtered_safety']} Safety"
            )
            logger.info(summary)
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
            
            # 处理不带 T 的日期格式 (如 2026-02-23)
            if 'T' not in end_time_str:
                end_time_str += 'T23:59:59'
            
            # 确保 ISO 格式带时区标识
            if not end_time_str.endswith('Z') and '+' not in end_time_str:
                end_time_str += 'Z'

            end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            hours_to_end = (end_time - now).total_seconds() / 3600

            # 必须在设定的极短线窗口内
            if settings.MIN_HOURS_TO_EXPIRY <= hours_to_end <= settings.MAX_HOURS_TO_EXPIRY:
                return True
            return False
        except Exception as e:
            logger.debug(f"Time parsing error for {market.get('question')}: {e}")
            return False

    async def _check_safety_locks(self, market: Dict) -> bool:
        """
        流动性锁 + 动量趋势过滤 (Momentum Filter)
        """
        token_id = market.get('token_id')
        if not token_id: return False
        
        try:
            # A. 流动性深度检查
            ob = await asyncio.get_event_loop().run_in_executor(None, self.client.get_order_book, token_id)
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
            # 采用 Gamma API 中的 oneDayPriceChange 字段作为动量指标
            price_change = market.get('oneDayPriceChange')
            if price_change is not None:
                # 核心判断：若过去24小时跌幅超过容忍度 -> 视为下跌趋势，拒绝
                if float(price_change) < -settings.MAX_PRICE_DROP_TOLERANCE:
                    logger.warning(f"Momentum Rejected: {token_id} (Price drop: {price_change} < -{settings.MAX_PRICE_DROP_TOLERANCE})")
                    return False
                
            return True
        except Exception as e:
            logger.error(f"Safety check error: {e}")
            return False

    async def fetch_active_markets(self) -> List[Dict]:
        import requests
        from datetime import datetime, timezone, timedelta
        try:
            markets = []
            limit = 100
            offset = 0
            max_pages = 50 # 允许拉取更多页，但由于有时间过滤，通常几页就结束了
            
            loop = asyncio.get_event_loop()
            now = datetime.now(timezone.utc)
            min_date = (now + timedelta(hours=settings.MIN_HOURS_TO_EXPIRY)).strftime('%Y-%m-%dT%H:%M:%SZ')
            max_date = (now + timedelta(hours=settings.MAX_HOURS_TO_EXPIRY)).strftime('%Y-%m-%dT%H:%M:%SZ')
            
            logger.debug(f"Fetching events expiring between {min_date} and {max_date}")

            for page in range(max_pages):
                url = f"https://gamma-api.polymarket.com/events?active=true&closed=false&end_date_min={min_date}&end_date_max={max_date}&limit={limit}&offset={offset}"
                resp = await loop.run_in_executor(None, requests.get, url)
                
                if resp.status_code != 200:
                    logger.error(f"Gamma API returned {resp.status_code}: {resp.text}")
                    break
                    
                events = resp.json()
                if not events:
                    break # 没有更多数据了
                    
                for event in events:
                    event_tags = event.get('tags', [])
                    for m in event.get('markets', []):
                        # Flatten necessary fields
                        m['category'] = event.get('category', 'Unknown')
                        m['tags'] = event_tags # 将事件的标签传递给市场对象
                        m['end_date_iso'] = m.get('endDateIso', m.get('endDate'))
                        m['condition_id'] = m.get('conditionId')
                        m['oneDayPriceChange'] = m.get('oneDayPriceChange', 0)
                        
                        # Extract YES token ID
                        clob_ids = m.get('clobTokenIds')
                        if clob_ids:
                            import json
                            try:
                                parsed_ids = json.loads(clob_ids)
                                if isinstance(parsed_ids, list) and len(parsed_ids) > 0:
                                    m['token_id'] = parsed_ids[0]
                            except: pass
                        
                        if m.get('token_id'):
                            m['time_class'] = "A"
                            markets.append(m)
                
                offset += limit
                
            return markets
        except Exception as e:
            logger.error(f"Failed to fetch from Gamma API: {e}")
            return []
