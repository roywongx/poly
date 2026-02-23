from .base_bot import BaseBot
from src.config import settings

class ArbBot(BaseBot):
    def __init__(self):
        super().__init__(
            name="Arb-V1",
            params={
                "min_price": 0.60,
                "max_price": 0.99,
                "depth_multiplier": 10 # Needs strong depth to ensure quick exit
            }
        )

    async def analyze(self, market: dict, ob_bids: list) -> dict:
        if not ob_bids: return {"action": "skip"}
        
        bids = ob_bids[:3] # look deeper
        best_bid = float(bids[0].price)
        
        if not (self.params["min_price"] <= best_bid <= self.params["max_price"]):
            return {"action": "skip"}
            
        total_depth = sum(float(b.size) * float(b.price) for b in bids)
        if total_depth < (settings.ORDER_AMOUNT_USD * self.params["depth_multiplier"]):
            return {"action": "skip"}
            
        # Try to bid slightly higher to grab
        return {
            "action": "buy",
            "confidence": best_bid * 0.8,
            "target_price": round(best_bid + 0.002, 3), # more aggressive pricing
            "reasoning": f"Arb entry at {best_bid}"
        }
