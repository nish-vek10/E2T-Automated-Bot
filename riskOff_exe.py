# ==== RISK OFF GUI ==== #

import MetaTrader5 as mt5
from baseClass import MT5Trader

def main():
    mt5.initialize()
    trader = MT5Trader()
    risk_percent = 0.25

    assets = [
        ("NDX", mt5.ORDER_TYPE_SELL, 1000),
        ("SP500", mt5.ORDER_TYPE_SELL, 500),
        ("GDAXI", mt5.ORDER_TYPE_SELL, 1000),
        ("USDJPY", mt5.ORDER_TYPE_BUY, 150),
        ("CHFJPY", mt5.ORDER_TYPE_BUY, 150),
        ("XAUUSD", mt5.ORDER_TYPE_BUY, 5000),
        ("EURUSD", mt5.ORDER_TYPE_SELL, 150),
    ]

    for symbol, order_type, sl in assets:
        lot = trader.calculate_lot_size(symbol, sl, risk_percent)
        if lot > 0:
            trader.place_order(symbol, order_type, lot, sl, comment="RiskOffAuto")

    trader.shutdown()
    mt5.shutdown()

if __name__ == "__main__":
    main()
