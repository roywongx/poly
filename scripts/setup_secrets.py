import keyring
import getpass

def setup():
    service_id = "polymarket_bot"
    
    print("--- PolyMarket Bot Secure Credential Setup ---")
    
    # 只需要存储最敏感的 4 个字段
    secrets = {
        "EOA_PRIVATE_KEY": "Your Ethereum Private Key (without 0x)",
        "CLOB_API_KEY": "Polymarket L2 API Key",
        "CLOB_API_SECRET": "Polymarket L2 API Secret",
        "CLOB_PASSPHRASE": "Polymarket L2 Passphrase"
    }
    
    for key, description in secrets.items():
        value = getpass.getpass(f"Enter {key} ({description}): ")
        if value:
            keyring.set_password(service_id, key, value)
            print(f"Successfully saved {key} to system keyring.")
        else:
            print(f"Skipped {key}.")

    print("
Setup Complete. You can now safely delete the values from your .env file.")

if __name__ == "__main__":
    setup()
