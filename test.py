import MetaTrader5 as mt5

# Try to initialize MT5 terminal
if not mt5.initialize():
    print("Initialization failed")
    quit()

# Try to get account info
account = mt5.account_info()
if account is None:
    print("❌ Failed to retrieve account info")
else:
    print("✅ Connected successfully!")
    print(f"Login: {account.login}, Balance: {account.balance}")

mt5.shutdown()
