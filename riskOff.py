
#####  R-I-S-K  O-F-F  #####

from baseClass import MT5Trader
import MetaTrader5 as mt5
import threading

risk_off_assets = [
    ("SP500.i", mt5.ORDER_TYPE_SELL, 1500),         # SPX SHORT (1000 = $10)
    ("NAS100.i", mt5.ORDER_TYPE_SELL, 400),         # NAS SHORT (1000 = $10)
    ("GER40.i", mt5.ORDER_TYPE_SELL, 1000),         # DAX SHORT (1000 = €10)
    ("USDJPY", mt5.ORDER_TYPE_BUY, 100),            # USD LONG (100 = 0.1 JPY)
    ("CHFJPY", mt5.ORDER_TYPE_BUY, 100),            # CFH LONG (100 = 0.1 JPY)
    ("XAUUSD", mt5.ORDER_TYPE_BUY, 500),            # GOLD LONG (1000 = $10)
    ("XAGUSD", mt5.ORDER_TYPE_BUY, 100),            # SILVER LONG (100 = $0.1)
]

# Create trader instance
trader = MT5Trader()
risk_percent = 0.25  # % of account balance to risk per trade

# Thread wrapper
def execute_trade(asset):
    symbol, order_type, sl = asset
    lot = trader.calculate_lot_size(symbol, sl, risk_percent)
    trader.place_order(symbol, order_type, lot, sl, comment="RiskOffAuto")

# Start all trades in parallel threads
threads = []
for asset in risk_off_assets:
    t = threading.Thread(target=execute_trade, args=(asset,))
    t.start()
    threads.append(t)

# Wait for all threads to complete
for t in threads:
    t.join()

# Shutdown connection
trader.shutdown()

