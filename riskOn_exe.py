# ==== RISK ON GUI ==== #

import MetaTrader5 as mt5
from baseClass import MT5Trader

def main():
    mt5.initialize()
    trader = MT5Trader()
    risk_percent = 0.25

    assets = [
        ("NAS100.i", mt5.ORDER_TYPE_BUY, 1000),
        ("SP500.i", mt5.ORDER_TYPE_BUY, 500),
        ("GER40.i", mt5.ORDER_TYPE_BUY, 1000),
        ("UK100.i", mt5.ORDER_TYPE_BUY, 1000),
        ("COPPER-C", mt5.ORDER_TYPE_BUY, 100),
        ("USDJPY", mt5.ORDER_TYPE_SELL, 150),
        ("EURUSD", mt5.ORDER_TYPE_BUY, 150),
    ]

    for symbol, order_type, sl in assets:
        lot = trader.calculate_lot_size(symbol, sl, risk_percent)
        if lot > 0:
            trader.place_order(symbol, order_type, lot, sl, comment="RiskOnAuto")

    trader.shutdown()
    mt5.shutdown()

if __name__ == "__main__":
    main()
