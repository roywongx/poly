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

    try:
        # 使用最新版 SDK 推荐的初始化方式
        print("\n步骤 2: 正在初始化 L2 客户端...")
        client = ClobClient(
            host=host,
            chain_id=chain_id,
            key=pk
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

        print("步骤 4: 正在申请 API 交易凭证...")
        try:
            creds = client.create_api_key()
            ak = creds.api_key
            as_ = creds.api_secret
            ap = creds.api_passphrase
        except Exception as e:
            if "400" in str(e) or "already exists" in str(e).lower():
                print("\n" + "!"*40)
                print("错误：无法创建密钥。这通常意味着您的 API Key 已存在。")
                print("请务必执行以下手动操作：")
                print("1. 访问 https://polymarket.com/settings/api")
                print("2. 点击红色按钮 'Delete API Key' 删除现有的。")
                print("3. 重新运行此脚本，即可自动生成并保存新的。")
                print("!"*40)
                return
            else:
                raise e

        print("\n步骤 5: 正在安全存储...")
        keyring.set_password(service_id, "EOA_PRIVATE_KEY", pk)
        keyring.set_password(service_id, "CLOB_API_KEY", ak)
        keyring.set_password(service_id, "CLOB_API_SECRET", as_)
        keyring.set_password(service_id, "CLOB_PASSPHRASE", ap)

        print("\n" + "√"*10 + " 配置成功！ " + "√"*10)
        print(f"API Key: {ak}")
        print("您现在可以直接运行机器人：python -m src.main")

    except Exception as e:
        print(f"\n[致命错误] {e}")

if __name__ == "__main__":
    onboard()
