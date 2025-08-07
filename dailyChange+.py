# ==== DAILY CHANGE + ==== #

"""
ISM Services PMI
Forecast: 51.5      Previous: 50.8

'Actual' greater than 'Forecast' is good for currency
"""

import MetaTrader5 as mt5
from baseClass import MT5Trader

def main():
    mt5.initialize()
    trader = MT5Trader()
    risk_percent = 0.25

    assets = [
        ("UK100.i", mt5.ORDER_TYPE_BUY, 1000),
        ("GBPUSD", mt5.ORDER_TYPE_SELL, 150),
        ("EURGBP", mt5.ORDER_TYPE_BUY, 150),
    ]

    for symbol, order_type, sl in assets:
        lot = trader.calculate_lot_size(symbol, sl, risk_percent)
        if lot > 0:
            trader.place_order(symbol, order_type, lot, sl, comment="RiskOffAuto")

    trader.shutdown()
    mt5.shutdown()

if __name__ == "__main__":
    main()
