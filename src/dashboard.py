import os
import json
import asyncio
import subprocess
import psutil
from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import dotenv_values, set_key
from pydantic import BaseModel

app = FastAPI(title="PolyMarket Arb Bot Dashboard")

# Static files (CSS, JS)
os.makedirs("src/static", exist_ok=True)
os.makedirs("src/templates", exist_ok=True)
app.mount("/static", StaticFiles(directory="src/static"), name="static")
templates = Jinja2Templates(directory="src/templates")

ALLOWED_CONFIG_KEYS = [
    "ORDER_AMOUNT_USD", 
    "GLOBAL_MAX_POSITIONS", 
    "MAX_ACTIVE_POSITIONS_PER_CATEGORY", 
    "ENTRY_PRICE_MIN", 
    "MAX_HOURS_TO_EXPIRY",
    "STOP_LOSS_L1_TRIGGER",
    "STOP_LOSS_L2_TRIGGER",
    "POISON_KEYWORDS",
    "EXCLUDED_CATEGORIES"
]

class ConfigUpdate(BaseModel):
    key: str
    value: str

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

BOT_PROCESS_NAME = "src.main"

def is_bot_running() -> bool:
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline')
            if cmdline and any(BOT_PROCESS_NAME in cmd for cmd in cmdline):
                # Ensure we don't count the dashboard itself if it's called with src.main (unlikely but safe)
                if any("dashboard.py" in cmd for cmd in cmdline):
                    continue
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return False

def start_bot():
    print("\n[DASHBOARD] Triggering Bot Startup...")
    
    # 1. Force cleanup existing bot processes first
    stop_bot()
    import time
    time.sleep(1) 
    
    try:
        # 2. Resolve absolute paths
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        python_exe = os.path.join(base_dir, "venv", "Scripts", "python.exe")
        
        if not os.path.exists(python_exe):
            python_exe = sys.executable # Use current python if venv not found
        
        print(f"[DASHBOARD] Executing: {python_exe} -m src.main")
        
        # 3. Launch with fresh console and environment
        env = os.environ.copy()
        env["PYTHONPATH"] = base_dir
        
        # Start bot as a completely independent process
        subprocess.Popen(
            [python_exe, "-m", "src.main"],
            cwd=base_dir,
            env=env,
            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0,
            stdout=None, 
            stderr=None
        )
        print("[DASHBOARD] Bot process spawned successfully.")
    except Exception as e:
        print(f"[DASHBOARD] FATAL ERROR during startup: {e}")

def stop_bot():
    print("[DASHBOARD] Scanning for existing bot processes to stop...")
    count = 0
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline')
            if cmdline and any(BOT_PROCESS_NAME in cmd for cmd in cmdline):
                print(f"[DASHBOARD] Stopping ghost process PID {proc.info['pid']}")
                proc.terminate()
                count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    if count > 0:
        print(f"[DASHBOARD] Cleaned up {count} processes.")
    else:
        print("[DASHBOARD] No existing bot processes found.")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/status")
async def get_status():
    running = is_bot_running()
    
    # Read bot state if available
    state = {}
    if os.path.exists("bot_state.json"):
        try:
            with open("bot_state.json", "r", encoding="utf-8") as f:
                state = json.load(f)
        except Exception:
            pass

    # Read latest logs
    logs = []
    log_dir = "logs"
    if os.path.exists(log_dir):
        log_files = [os.path.join(log_dir, f) for f in os.listdir(log_dir) if f.endswith(".log")]
        if log_files:
            latest_log = max(log_files, key=os.path.getmtime)
            try:
                with open(latest_log, "r", encoding="utf-8") as f:
                    # Get last 1000 lines for better context
                    lines = f.readlines()
                    logs = lines[-1000:]
            except Exception:
                pass

    return JSONResponse({
        "status": "running" if running else "stopped",
        "state": state,
        "logs": logs
    })

@app.post("/api/bot/start")
async def api_start_bot(background_tasks: BackgroundTasks):
    background_tasks.add_task(start_bot)
    return {"message": "Starting bot..."}

@app.post("/api/bot/stop")
async def api_stop_bot(background_tasks: BackgroundTasks):
    background_tasks.add_task(stop_bot)
    return {"message": "Stopping bot..."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
