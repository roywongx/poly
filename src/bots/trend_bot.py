from .base_bot import BaseBot
from src.config import settings

class TrendBot(BaseBot):
    def __init__(self):
        super().__init__(
            name="Trend-V1",
            params={
                "min_price": 0.70,
                "max_price": 0.99,
                "depth_multiplier": 5,
                "min_momentum": 0.05 # Needs +5% positive momentum in 24h
            }
        )

    async def analyze(self, market: dict, ob_bids: list) -> dict:
        if not ob_bids: return {"action": "skip"}
        
        bids = ob_bids[:2]
        best_bid = float(bids[0].price)
        
        if not (self.params["min_price"] <= best_bid <= self.params["max_price"]):
            return {"action": "skip"}
            
        total_depth = sum(float(b.size) * float(b.price) for b in bids)
        if total_depth < (settings.ORDER_AMOUNT_USD * self.params["depth_multiplier"]):
            return {"action": "skip"}
            
        price_change = market.get('oneDayPriceChange', 0)
        if price_change is None or float(price_change) < self.params["min_momentum"]:
            return {"action": "skip"}
            
        return {
            "action": "buy",
            "confidence": best_bid * 0.9, # Weight it slightly lower than sniper
            "target_price": round(best_bid + 0.001, 3),
            "reasoning": f"Trend follow at {best_bid} (Mom: {price_change})"
        }
