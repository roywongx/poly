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

# Ensure directories exist
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
            if cmdline and any(BOT_PROCESS_NAME in cmd for cmd in cmdline):
                # Ensure it's the bot, not the dashboard
                if any("dashboard.py" in cmd for cmd in cmdline):
                    continue
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return False

def start_bot():
    print("\n>>> [DASHBOARD] RESTARTING BOT ENGINE...")
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
            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0,
            stdout=None, 
            stderr=None
        )
        print(">>> [LAUNCH] Bot spawned successfully in a new terminal.")
    except Exception as e:
        print(f">>> [LAUNCH] ERROR: {e}")

def stop_bot():
    print(">>> [DASHBOARD] SCANNING FOR INSTANCES TO STOP...")
    count = 0
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline')
            if cmdline and any(BOT_PROCESS_NAME in cmd for cmd in cmdline):
                if any("dashboard.py" in cmd for cmd in cmdline): continue
                print(f">>> [KILL] Stopping PID {proc.info['pid']}")
                proc.terminate()
                count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    print(f">>> [DASHBOARD] Cleaned up {count} ghost processes.")

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

    logs = []
    log_dir = os.path.join(BASE_DIR, "logs")
    if os.path.exists(log_dir):
        files = [os.path.join(log_dir, f) for f in os.listdir(log_dir) if f.endswith(".log")]
        if files:
            latest = max(files, key=os.path.getmtime)
            try:
                with open(latest, "r", encoding="utf-8") as f:
                    logs = f.readlines()[-1000:]
            except: pass

    return JSONResponse({"status": "running" if running else "stopped", "state": state, "logs": logs})

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
