# ==== OIL LONG GUI ==== #

import MetaTrader5 as mt5
from baseClass import MT5Trader

def main():
    mt5.initialize()
    trader = MT5Trader()
    risk_percent = 0.25

    assets = [
        ("UKOUSD", mt5.ORDER_TYPE_BUY, 100),     # BRENT OIL - (100 = $0.1)
        ("USOUSD", mt5.ORDER_TYPE_BUY, 100),     # CRUDE OIL - (100 = $0.1)
        ("USDCAD",mt5.ORDER_TYPE_SELL, 50)
    ]

    for symbol, order_type, sl in assets:
        lot = trader.calculate_lot_size(symbol, sl, risk_percent)
        if lot > 0:
            trader.place_order(symbol, order_type, lot, sl, comment="OilLongAuto")

    trader.shutdown()
    mt5.shutdown()

if __name__ == "__main__":
    main()