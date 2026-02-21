import keyring
import getpass
from pyclob_client.client import ClobClient
from loguru import logger
import sys

def onboard():
    service_id = "polymarket_bot"
    host = "https://clob.polymarket.com"
    chain_id = 137

    print("\n" + "="*50)
    print("   PolyMarket Bot One-Click Onboarding V2.0")
    print("="*50)
    print("此脚本将使用您的私钥自动生成并保存 L2 交易凭证。\n")

    # 1. 获取私钥
    pk = getpass.getpass("步骤 1: 请粘贴您的钱包私钥 (不带 0x): ").strip()
    if not pk:
        print("错误: 必须输入私钥。")
        return

    try:
        # 2. 初始化客户端 (仅使用私钥进行签名)
        print("\n步骤 2: 正在连接 Polymarket CLOB...")
        # 注意：这里我们只传入私钥，让 SDK 自动处理签名器
        client = ClobClient(
            host=host,
            private_key=pk,
            chain_id=chain_id
        )

        # 3. 申请 API 凭证
        print("步骤 3: 正在向服务器申请新的 API 交易凭证...")
        try:
            # 调用 SDK 创建 API Key
            creds = client.create_api_key()
            
            # 解析返回结果 (兼容对象和字典格式)
            if isinstance(creds, dict):
                api_key = creds.get('apiKey')
                api_secret = creds.get('secret')
                api_passphrase = creds.get('passphrase')
            else:
                api_key = creds.api_key
                api_secret = creds.api_secret
                api_passphrase = creds.api_passphrase

        except Exception as api_err:
            error_msg = str(api_err)
            if "already exists" in error_msg.lower():
                print("\n[提示] 您之前已经为该钱包创建过 API 密钥了。")
                print("由于安全原因，Polymarket 不允许重复获取 Secret。")
                print("-" * 40)
                print("请执行以下操作：")
                print("1. 访问 https://polymarket.com/settings/api")
                print("2. 点击 'Delete API Key' 删除旧的。")
                print("3. 重新运行此脚本，即可自动生成并保存新的。")
                print("-" * 40)
                return
            else:
                raise api_err

        # 4. 自动保存到 Keyring
        print("\n步骤 4: 正在加密并存入系统保险箱...")
        keyring.set_password(service_id, "EOA_PRIVATE_KEY", pk)
        keyring.set_password(service_id, "CLOB_API_KEY", api_key)
        keyring.set_password(service_id, "CLOB_API_SECRET", api_secret)
        keyring.set_password(service_id, "CLOB_PASSPHRASE", api_passphrase)

        print("\n" + "√"*10 + " 配置成功！ " + "√"*10)
        print(f"您的 API Key 为: {api_key}")
        print("所有的敏感信息（私钥、Secret）已安全加密存储。")
        print("现在您可以直接运行机器人：python -m src.main")

    except Exception as e:
        print(f"\n[发生错误] {e}")
        print("请检查：1. 私钥是否正确；2. 网络是否能访问 Polymarket；3. 钱包里是否有极少量 MATIC。")

if __name__ == "__main__":
    onboard()
