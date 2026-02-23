import os
import json
import asyncio
import subprocess
import psutil
import sys
from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import dotenv_values, set_key
from pydantic import BaseModel

app = FastAPI(title="PolyMarket Arb Bot Dashboard")

# Constants
BOT_PROCESS_NAME = "src.main"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src import db
os.makedirs(os.path.join(BASE_DIR, "src", "static"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "src", "templates"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)

# Mount paths
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "src", "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "src", "templates"))

ALLOWED_CONFIG_KEYS = [
    "ORDER_AMOUNT_USD", 
    "GLOBAL_MAX_POSITIONS", 
    "MAX_ACTIVE_POSITIONS_PER_CATEGORY", 
    "ENTRY_PRICE_MIN", 
    "MAX_HOURS_TO_EXPIRY",
    "TAKE_PROFIT_PRICE",
    "STOP_LOSS_L1_TRIGGER",
    "STOP_LOSS_L2_TRIGGER",
    "POISON_KEYWORDS",
    "EXCLUDED_CATEGORIES"
]

class ConfigUpdate(BaseModel):
    key: str
    value: str

def is_bot_running() -> bool:
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline')
            if not cmdline: continue
            cmd_str = " ".join(cmdline).lower()
            if "python" in cmd_str and "src.main" in cmd_str:
                if "dashboard.py" in cmd_str: continue
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return False

def start_bot():
    print("\n>>> [DASHBOARD] ENGINE IGNITION SEQUENCE START")
    stop_bot()
    import time
    time.sleep(1)
    
    try:
        python_exe = sys.executable 
        print(f">>> [LAUNCH] Executing: {python_exe} -m src.main")
        
        env = os.environ.copy()
        env["PYTHONPATH"] = BASE_DIR
        
        subprocess.Popen(
            [python_exe, "-m", "src.main"],
            cwd=BASE_DIR,
            env=env,
            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
        )
        print(">>> [LAUNCH] Success. Bot spawned in new console.")
    except Exception as e:
        print(f">>> [LAUNCH] ERROR: {e}")

def stop_bot():
    print(">>> [DASHBOARD] PERFORMING SYSTEM SWEEP...")
    count = 0
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline')
            if not cmdline: continue
            cmd_str = " ".join(cmdline).lower()
            if "python" in cmd_str and "src.main" in cmd_str:
                if "dashboard.py" in cmd_str: continue
                print(f">>> [KILL] Target PID {proc.info['pid']} neutralized.")
                proc.kill()
                count += 1
        except: pass
    print(f">>> [DASHBOARD] {count} instances cleaned.")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/config")
async def get_config():
    env_vars = dotenv_values(".env")
    return JSONResponse({k: env_vars.get(k, "") for k in ALLOWED_CONFIG_KEYS})

@app.post("/api/config")
async def update_config(config: ConfigUpdate):
    if config.key in ALLOWED_CONFIG_KEYS:
        set_key(".env", config.key, str(config.value))
        return {"status": "success"}
    return {"status": "error", "message": "Invalid key"}, 400

@app.get("/api/status")
async def get_status():
    running = is_bot_running()
    state = {}
    state_path = os.path.join(BASE_DIR, "bot_state.json")
    if os.path.exists(state_path):
        try:
            with open(state_path, "r", encoding="utf-8") as f:
                state = json.load(f)
        except: pass

    # Read logs via LATEST pointer for 1000% accuracy
    logs = []
    latest_ptr = os.path.join(BASE_DIR, "logs", "LATEST")
    if os.path.exists(latest_ptr):
        try:
            with open(latest_ptr, "r", encoding="utf-8") as f:
                current_log_path = f.read().strip()
                # If bot_... is stored, join it with BASE_DIR
                full_log_path = os.path.join(BASE_DIR, current_log_path)
                if os.path.exists(full_log_path):
                    with open(full_log_path, "r", encoding="utf-8") as lf:
                        logs = lf.readlines()[-1000:]
        except: pass

    return JSONResponse({"status": "running" if running else "stopped", "state": state, "logs": logs})

@app.get("/api/arena/bots")
async def get_arena_bots():
    try:
        bots = db.get_active_bots()
        for b in bots:
            perf = db.get_bot_performance(b["name"], hours=24)
            b.update(perf)
        return JSONResponse({"bots": bots})
    except Exception as e:
        print(f"Error fetching bots: {e}")
        return JSONResponse({"bots": []})

@app.get("/api/arena/trades")
async def get_arena_trades():
    try:
        with db.get_conn() as conn:
            rows = conn.execute('''
                SELECT * FROM trades 
                ORDER BY created_at DESC LIMIT 50
            ''').fetchall()
            return JSONResponse({"trades": [dict(r) for r in rows]})
    except Exception as e:
        print(f"Error fetching trades: {e}")
        return JSONResponse({"trades": []})

@app.post("/api/bot/start")
async def api_start_bot(background_tasks: BackgroundTasks):
    background_tasks.add_task(start_bot)
    return {"message": "Starting..."}

@app.post("/api/bot/stop")
async def api_stop_bot(background_tasks: BackgroundTasks):
    background_tasks.add_task(stop_bot)
    return {"message": "Stopping..."}

if __name__ == "__main__":
    import uvicorn
    # EXPLICITLY use 127.0.0.1 as requested for local stability
    print("\n" + "="*50)
    print("   POLYMARKET SCALPEL DASHBOARD STARTING")
    print("   URL: http://127.0.0.1:8000")
    print("="*50 + "\n")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
