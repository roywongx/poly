import math
from loguru import logger
from datetime import datetime
import json
from . import db

PRICE_BUCKETS = [
    ("price_very_low", 0.0, 0.30),
    ("price_low", 0.30, 0.45),
    ("price_neutral", 0.45, 0.55),
    ("price_high", 0.55, 0.70),
    ("price_very_high", 0.70, 1.01),
]

def extract_features(market_price, hour_utc=None):
    features = []
    for name, lo, hi in PRICE_BUCKETS:
        if lo <= market_price < hi:
            features.append(name)
            break
            
    if hour_utc is None:
        hour_utc = datetime.utcnow().hour
        
    hour_bucket = f"hour_{hour_utc // 6 * 6}" # 0, 6, 12, 18
    features.append(hour_bucket)
    
    return features

def get_learned_bias(bot_name, features, prior_yes=0.5):
    with db.get_conn() as conn:
        rows = conn.execute(
            "SELECT feature_key, wins, losses FROM bot_learning WHERE bot_name=?",
            (bot_name,)
        ).fetchall()

    learned = {r["feature_key"]: (r["wins"], r["losses"]) for r in rows}
    log_odds = math.log(prior_yes / (1 - prior_yes)) if 0 < prior_yes < 1 else 0

    for feat in features:
        if feat not in learned: continue
        wins, losses = learned[feat]
        total = wins + losses
        if total < 2: continue

        feat_wr = (wins + 1) / (total + 2)
        strength = min(math.sqrt(total) * 0.5, 3.0)
        feat_log_odds = math.log(feat_wr / (1 - feat_wr))
        log_odds += feat_log_odds * strength * 0.35

    yes_bias = 1.0 / (1.0 + math.exp(-log_odds))
    return max(0.05, min(0.95, yes_bias))

def record_outcome(bot_name, features, side, won):
    with db.get_conn() as conn:
        for feat in features:
            if side == "yes":
                if won:
                    conn.execute('''
                        INSERT INTO bot_learning (bot_name, feature_key, wins, losses)
                        VALUES (?, ?, 1, 0)
                        ON CONFLICT(bot_name, feature_key) DO UPDATE SET wins=wins+1, updated_at=CURRENT_TIMESTAMP
                    ''', (bot_name, feat))
                else:
                    conn.execute('''
                        INSERT INTO bot_learning (bot_name, feature_key, wins, losses)
                        VALUES (?, ?, 0, 1)
                        ON CONFLICT(bot_name, feature_key) DO UPDATE SET losses=losses+1, updated_at=CURRENT_TIMESTAMP
                    ''', (bot_name, feat))
            else:
                if won:
                    conn.execute('''
                        INSERT INTO bot_learning (bot_name, feature_key, wins, losses)
                        VALUES (?, ?, 0, 1)
                        ON CONFLICT(bot_name, feature_key) DO UPDATE SET losses=losses+1, updated_at=CURRENT_TIMESTAMP
                    ''', (bot_name, feat))
                else:
                    conn.execute('''
                        INSERT INTO bot_learning (bot_name, feature_key, wins, losses)
                        VALUES (?, ?, 1, 0)
                        ON CONFLICT(bot_name, feature_key) DO UPDATE SET wins=wins+1, updated_at=CURRENT_TIMESTAMP
                    ''', (bot_name, feat))
