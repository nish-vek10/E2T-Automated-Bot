
#####  R-I-S-K  O-N  #####

from baseClass import MT5Trader
import MetaTrader5 as mt5
import threading

# Format: (Symbol, OrderType, SL (points))
risk_on_assets = [
    ("NAS100.i", mt5.ORDER_TYPE_BUY, 1500),     # NAS100 LONG (1000 = $10)
    ("SP500.i", mt5.ORDER_TYPE_BUY, 500),       # SPX LONG (1000 = $10)
    ("GER40.i", mt5.ORDER_TYPE_BUY, 1000),      # DAX LONG (1000 = €10)
    ("COPPER-C", mt5.ORDER_TYPE_BUY, 100),      # COPPER LONG (100 = $0.01)
    ("AUDUSD", mt5.ORDER_TYPE_BUY, 100),        # FX AUD/USD LONG (100 = $0.001)
    ("USDJPY", mt5.ORDER_TYPE_BUY, 100),        # FX USD/JPY LONG (100 = 0.1 JPY)
]

# Create trader instance
trader = MT5Trader()
risk_percent = 0.25  # % of account balance to risk per trade

# Thread wrapper
def execute_trade(asset):
    symbol, order_type, sl = asset
    lot = trader.calculate_lot_size(symbol, sl, risk_percent)
    trader.place_order(symbol, order_type, lot, sl, comment="RiskOnAuto")

# Start all trades in parallel threads
threads = []
for asset in risk_on_assets:
    t = threading.Thread(target=execute_trade, args=(asset,))
    t.start()
    threads.append(t)

# Wait for all threads to complete
for t in threads:
    t.join()

# Shutdown connection
trader.shutdown()

