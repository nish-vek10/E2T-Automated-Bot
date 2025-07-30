
#####  D-A-I-L-Y  #####

from baseClass import MT5Trader
import MetaTrader5 as mt5


# TUESDAY 20TH MAY
# AUD - CASH RATE (CUT EXPECTED FROM 4.10% TO 3.85%)
# CAD - CPI (M/M 0.3% PRE - EXPECTED

risk_on_assets = [
    ("EURUSD", mt5.ORDER_TYPE_BUY, 0.1, 1000, 4000),  # NAS100 LONG
    ("EURGBP", mt5.ORDER_TYPE_BUY, 0.1, 1000, 3000),   # SPX LONG
    ("GER40.i", mt5.ORDER_TYPE_BUY, 0.1, 1000, 3000),   # DAX LONG
]

trader = MT5Trader()

# === Execute all RISK ON trades in loop ===
for symbol, order_type, lot, sl in risk_on_assets:
    trader.place_order(symbol, order_type, lot, sl_points=sl, comment="RiskOnAuto")

trader.shutdown()
