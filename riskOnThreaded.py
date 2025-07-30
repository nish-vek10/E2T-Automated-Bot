
#####  R-I-S-K  O-N  -  T-H-R-E-A-D-E-D #####

from baseClass import MT5Trader
import  MetaTrader5 as mt5
from datetime import datetime
from threading import Thread

from guiNEW2 import trade

risk_percent = 0.25

risk_on_assets = [
    ("NAS100.i", mt5.ORDER_TYPE_BUY, 1000, 4000),  # NAS100 LONG
    ("SP500.i", mt5.ORDER_TYPE_BUY, 1000, 3000),   # SPX LONG
    ("GER40.i", mt5.ORDER_TYPE_BUY, 1000, 3000),   # DAX LONG
    ("USOUSD", mt5.ORDER_TYPE_BUY, 300, 600),      # OIL LONG
    ("COPPER-C", mt5.ORDER_TYPE_BUY, 300, 700),    # COPPER LONG
    ("AUDUSD", mt5.ORDER_TYPE_BUY, 1000, 2500),    # FX AUD/USD LONG
    ("USDJPY", mt5.ORDER_TYPE_BUY, 100, 300),       # FX USD/JPY LONG
    ("VIX.i", mt5.ORDER_TYPE_SELL, 1000, 2000),    # VOLATILITY INDEX SHORT
]

trader = MT5Trader()
account_balance = trader.get_account_balance()

results = []

def execute_trade(symbol, order_type, sl, tp):
    tick, info = trader.get_tick_info(symbol)
    if not tick or not info:
        results.append((symbol, "⚠️ No tick/info"))
        return

    point_value = info.point
    lot = trader.calculate_lot(account_balance, risk_percent, sl, point_value)

    if lot < 0.01:
        results.append((symbol, "❌ Lot size too small"))
        return

    success = trader.place_order(symbol, order_type, lot, sl_points=sl, tp_points=tp, comment="RiskOnAuto")
    results.append((symbol, "✅ Success" if success else "❌ Failed"))

# === Multithreaded Execution ===
threads = []
for symbol, order_type, sl, tp in risk_on_assets:
    thread = Thread(target=execute_trade, args=(symbol, order_type, sl, tp))
    thread.start()
    threads.append(thread)

# Wait for all threads to finish
for thread in threads:
    thread.join()

# === Summary ===
print("\n=== [TRADE SUMMARY - MULTITHREADED] ===")
for symbol, status in results:
    print(f"{symbol}: {status}")

trader.shutdown()