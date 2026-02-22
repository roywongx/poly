import os
import subprocess
import sys
from dotenv import load_dotenv, set_key

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    print("=" * 50)
    print("   PolyMarket Arb Bot V7.0 - 管理控制台 (Management)")
    print("=" * 50)

def modify_settings():
    env_path = ".env"
    if not os.path.exists(env_path):
        print("❌ 错误: 未找到 .env 文件。请先运行 onboard_user.py")
        input("\n按回车继续...")
        return

    load_dotenv(env_path)
    
    params = {
        "ORDER_AMOUNT_USD": "单次下注金额 (USDC)",
        "MAX_ACTIVE_POSITIONS_PER_CATEGORY": "单个类别最大持仓数",
        "GLOBAL_MAX_POSITIONS": "全局最大持仓总数",
        "ENTRY_PRICE_MIN": "进场胜率下限 (0.0-1.0)",
        "MAX_HOURS_TO_EXPIRY": "最大剩余结算时间 (小时)",
        "POISON_KEYWORDS": "绝对不买的违禁词 (逗号隔开)",
        "EXCLUDED_CATEGORIES": "排除的高危分类 (逗号隔开)"
    }

    while True:
        clear_screen()
        print_header()
        print("\n--- 当前参数设置 ---")
        current_values = {}
        for key, desc in params.items():
            val = os.getenv(key, "未设置")
            current_values[key] = val
            print(f"[{key}] {desc}: {val}")
        
        print("\n[M] 修改参数 | [B] 返回主菜单")
        choice = input("\n请选择: ").strip().upper()

        if choice == 'B':
            break
        elif choice == 'M':
            key_to_mod = input("请输入要修改的参数键名: ").strip()
            if key_to_mod in params:
                new_val = input(f"请输入 {key_to_mod} 的新值: ").strip()
                if new_val:
                    set_key(env_path, key_to_mod, new_val)
                    os.environ[key_to_mod] = new_val # 更新当前进程的环境变量
                    print(f"✅ {key_to_mod} 已更新为 {new_val}")
                    input("\n按回车继续...")
            else:
                print("❌ 无效的键名")
                input("\n按回车继续...")

def start_dashboard():
    print("\n--- 正在启动网页控制面板 (Dashboard) ---")
    print("👉 启动后请在浏览器访问: http://localhost:8000")
    print("👉 按 Ctrl+C 停止面板服务并返回菜单\n")
    try:
        subprocess.run(["venv\\Scripts\\python.exe", "src/dashboard.py"])
    except KeyboardInterrupt:
        pass

def update_program():
    print("\n--- 正在从 GitHub 更新程序 ---")
    try:
        subprocess.run(["git", "pull"], check=True)
        print("✅ 更新成功！")
    except Exception as e:
        print(f"❌ 更新失败: {e}")
    input("\n按回车继续...")

def sync_github():
    print("\n--- 正在同步到 GitHub ---")
    commit_msg = input("请输入提交信息 (默认为 'Update config'): ").strip() or "Update config"
    try:
        subprocess.run(["git", "add", "."], check=True)
        # 检查是否包含敏感文件
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout
        if ".env" in status or "USER_GUIDE_PRIVATE.md" in status:
            print("⚠️ 警告: 检测到敏感文件 (.env 或 USER_GUIDE_PRIVATE.md) 准备提交！")
            confirm = input("确定要继续吗？(y/N): ").strip().lower()
            if confirm != 'y':
                print("操作已取消。请检查 .gitignore。")
                subprocess.run(["git", "reset"], check=True)
                input("\n按回车继续...")
                return

        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        subprocess.run(["git", "push"], check=True)
        print("✅ 同步成功！")
    except Exception as e:
        print(f"❌ 同步失败: {e}")
    input("\n按回车继续...")

def open_docs():
    while True:
        clear_screen()
        print_header()
        print("\n--- 说明文件修改 ---")
        print("1. 修改 公共 README.md (GitHub 展示)")
        print("2. 修改 本地私有 USER_GUIDE_PRIVATE.md (绝不上传)")
        print("B. 返回主菜单")
        
        choice = input("\n请选择: ").strip().upper()
        if choice == '1':
            os.system("notepad README.md" if os.name == 'nt' else "vi README.md")
        elif choice == '2':
            os.system("notepad USER_GUIDE_PRIVATE.md" if os.name == 'nt' else "vi USER_GUIDE_PRIVATE.md")
        elif choice == 'B':
            break

def main():
    while True:
        clear_screen()
        print_header()
        print("1. 🌐  启动网页控制面板 (Dashboard) - 推荐！")
        print("2. 🛠️  修改交易指标 (命令行调参)")
        print("3. 🔄  更新程序 (Git Pull)")
        print("4. ⬆️  同步到 GitHub (Git Push)")
        print("5. 📝  查看/修改说明文档")
        print("Q. 退出")
        
        choice = input("\n请选择操作: ").strip().upper()
        
        if choice == '1':
            start_dashboard()
        elif choice == '2':
            modify_settings()
        elif choice == '3':
            update_program()
        elif choice == '4':
            sync_github()
        elif choice == '5':
            open_docs()
        elif choice == 'Q':
            sys.exit()

if __name__ == "__main__":
    main()
