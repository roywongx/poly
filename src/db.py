import sqlite3
import json
import time
from pathlib import Path
from loguru import logger

DB_PATH = Path("arena.db")

def init_db():
    with get_conn() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bot_name TEXT,
                market_id TEXT,
                market_question TEXT,
                side TEXT,
                amount REAL,
                entry_price REAL,
                shares_bought REAL,
                confidence REAL,
                reasoning TEXT,
                trade_features TEXT,
                venue TEXT,
                mode TEXT,
                outcome TEXT,
                pnl REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS bot_learning (
                bot_name TEXT,
                feature_key TEXT,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (bot_name, feature_key)
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS bot_configs (
                name TEXT PRIMARY KEY,
                strategy_type TEXT,
                generation INTEGER,
                params TEXT,
                lineage TEXT,
                active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS arena_state (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def log_trade(bot_name, market_id, market_question, side, amount, entry_price, shares_bought, confidence, reasoning, features, venue, mode):
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO trades (bot_name, market_id, market_question, side, amount, entry_price, shares_bought, confidence, reasoning, trade_features, venue, mode)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (bot_name, market_id, market_question, side, amount, entry_price, shares_bought, confidence, reasoning, json.dumps(features) if features else None, venue, mode))
        return cursor.lastrowid

def resolve_trade(trade_id, outcome, pnl):
    with get_conn() as conn:
        conn.execute('''
            UPDATE trades SET outcome = ?, pnl = ?, resolved_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (outcome, pnl, trade_id))

def get_bot_performance(bot_name, hours=24):
    with get_conn() as conn:
        row = conn.execute('''
            SELECT 
                COUNT(*) as total_trades,
                SUM(CASE WHEN outcome = 'win' THEN 1 ELSE 0 END) as wins,
                SUM(pnl) as total_pnl
            FROM trades 
            WHERE bot_name = ? AND outcome IS NOT NULL AND created_at >= datetime('now', ?)
        ''', (bot_name, f'-{hours} hours')).fetchone()
        
        wins = row["wins"] or 0
        total = row["total_trades"] or 0
        return {
            "total_trades": total,
            "win_rate": wins / total if total > 0 else 0.0,
            "total_pnl": row["total_pnl"] or 0.0
        }

def save_bot_config(name, strategy_type, generation, params, lineage=None):
    with get_conn() as conn:
        conn.execute('''
            INSERT OR REPLACE INTO bot_configs (name, strategy_type, generation, params, lineage, active)
            VALUES (?, ?, ?, ?, ?, 1)
        ''', (name, strategy_type, generation, json.dumps(params), lineage))

def retire_bot(name):
    with get_conn() as conn:
        conn.execute('UPDATE bot_configs SET active = 0 WHERE name = ?', (name,))

def get_active_bots():
    with get_conn() as conn:
        rows = conn.execute('SELECT * FROM bot_configs WHERE active = 1').fetchall()
        return [dict(r) for r in rows]

init_db()
