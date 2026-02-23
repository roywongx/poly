from .base_bot import BaseBot
from src.config import settings

class SniperBot(BaseBot):
    def __init__(self):
        super().__init__(
            name="Sniper-V1",
            params={
                "min_price": 0.93,
                "max_price": 0.99,
                "depth_multiplier": 5,
                "max_drop": 0.02
            }
        )

    async def analyze(self, market: dict, ob_bids: list) -> dict:
        if not ob_bids: return {"action": "skip"}
        
        bids = ob_bids[:2]
        best_bid = float(bids[0].price)
        
        if not (self.params["min_price"] <= best_bid <= self.params["max_price"]):
            return {"action": "skip", "reasoning": f"Price {best_bid} out of range"}
            
        total_depth = sum(float(b.size) * float(b.price) for b in bids)
        if total_depth < (settings.ORDER_AMOUNT_USD * self.params["depth_multiplier"]):
            return {"action": "skip", "reasoning": "Low liquidity"}
            
        price_change = market.get('oneDayPriceChange', 0)
        if price_change is not None and float(price_change) < -self.params["max_drop"]:
            return {"action": "skip", "reasoning": f"Price drop {price_change} < -{self.params['max_drop']}"}
            
        return {
            "action": "buy",
            "confidence": best_bid,
            "target_price": round(best_bid + 0.001, 3),
            "reasoning": f"Sniper entry at {best_bid}"
        }
