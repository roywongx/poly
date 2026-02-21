import keyring
import getpass

def setup():
    service_id = "polymarket_bot"
    
    print("--- PolyMarket Bot Secure Credential Setup ---")
    
    # 存储最敏感的 4 个字段
    secrets = {
        "EOA_PRIVATE_KEY": "Your Ethereum Private Key (without 0x)",
        "CLOB_API_KEY": "Polymarket L2 API Key",
        "CLOB_API_SECRET": "Polymarket L2 API Secret",
        "CLOB_PASSPHRASE": "Polymarket L2 Passphrase"
    }
    
    for key, description in secrets.items():
        try:
            prompt = f"Enter {key} ({description}): "
            value = getpass.getpass(prompt)
            if value:
                keyring.set_password(service_id, key, value)
                print(f"Successfully saved {key} to system keyring.")
            else:
                print(f"Skipped {key}.")
        except Exception as e:
            print(f"Error saving {key}: {e}")

    print("\nSetup Complete. You can now safely delete the sensitive values from your .env file.")

if __name__ == "__main__":
    setup()
