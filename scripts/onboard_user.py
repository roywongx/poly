import keyring
import getpass
import sys
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import ApiCreds
from loguru import logger

def onboard():
    service_id = "polymarket_bot"
    host = "https://clob.polymarket.com"
    chain_id = 137

    print("\n" + "="*50)
    print("   PolyMarket Bot One-Click Onboarding V7.0")
    print("="*50)

    pk = getpass.getpass("步骤 1: 请粘贴您的钱包私钥 (不带 0x): ").strip()
    if not pk:
        return

    print("\n步骤 1.5: 您的 Polymarket 主钱包(如MetaMask)与 Profile 里显示的地址不同吗？(多半不同)")
    is_proxy = input("如果是(或使用Google/邮箱登录)，请输入 'y'，否则按回车: ").strip().lower() == 'y'
    funder = None
    sig_type = 0
    if is_proxy:
        print("\n请访问 https://polymarket.com/settings?tab=profile 找到您的【Address】(代理钱包，如 0x753...)")
        funder = input("请输入该钱包地址 (0x...): ").strip()
        print("\n您是使用哪种方式登录 Polymarket 的？")
        print("1. Google 或 邮箱 (Magic Link)")
        print("2. MetaMask / TokenPocket / 外部独立钱包 (通常选这个)")
        login_type = input("请输入 1 或 2: ").strip()
        if login_type == '1':
            sig_type = 1
        else:
            sig_type = 2

    try:
        # 使用最新版 SDK 推荐的初始化方式
        print("\n步骤 2: 正在初始化 L2 客户端...")
        client = ClobClient(
            host=host,
            chain_id=chain_id,
            key=pk,
            signature_type=sig_type,
            funder=funder
        )

        # 核心修复：先尝试激活 L2 账户
        print("步骤 3: 检查并激活 L2 交易账户 (Onboarding)...")
        try:
            # 这一步会发送签名消息激活 L2
            client.onboard_user()
            print("√ L2 账户已准备就绪。")
        except Exception as e:
            # 如果已经激活过，通常会报错，我们忽略它继续
            print(f"提示: L2 激活状态检查完成 (或已激活)。")

        print("步骤 4: 正在申请/派生 API 交易凭证...")
        try:
            creds = client.create_or_derive_api_creds()
            ak = creds.api_key
            as_ = creds.api_secret
            ap = creds.api_passphrase
        except Exception as e:
            if "400" in str(e) or "already exists" in str(e).lower():
                print("\n" + "!"*40)
                print("错误：无法通过代码直接创建密钥 (Error 400)。")
                print("原因可能是：1. 您还没在网页上创建 Builder Profile，或 2. 您的 API Key 已满/存在冲突。")
                print("请务必执行以下手动操作：")
                print("1. 访问最新管理页: https://polymarket.com/settings?tab=builder")
                print("2. 如果页面提示 'You don't have a builder profile yet'，请点击按钮创建一个 Profile。")
                print("3. 如果您看到 'Builder Keys' 并且已经有旧的 Key，请点击删除。")
                print("4. 搞定后，重新运行此脚本即可！")
                print("!"*40)
                return
            else:
                raise e

        print("\n步骤 5: 正在安全存储...")
        keyring.set_password(service_id, "EOA_PRIVATE_KEY", pk)
        keyring.set_password(service_id, "CLOB_API_KEY", ak)
        keyring.set_password(service_id, "CLOB_API_SECRET", as_)
        keyring.set_password(service_id, "CLOB_PASSPHRASE", ap)
        if funder:
            keyring.set_password(service_id, "FUNDER_ADDRESS", funder)
        else:
            try:
                keyring.delete_password(service_id, "FUNDER_ADDRESS")
            except Exception:
                pass
        keyring.set_password(service_id, "SIGNATURE_TYPE", str(sig_type))

        print("\n" + "√"*10 + " 配置成功！ " + "√"*10)
        print(f"API Key: {ak}")
        print("您现在可以直接运行机器人：python -m src.main")

    except Exception as e:
        print(f"\n[致命错误] {e}")

if __name__ == "__main__":
    onboard()
