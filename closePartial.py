#####  P-A-R-T-I-A-L   C-L-O-S-E  (50%)  #####

from baseClass import MT5Trader
import MetaTrader5 as mt5

# Initialize trader
trader = MT5Trader()

# Get all open positions
positions = mt5.positions_get()

if positions is None or len(positions) == 0:
    print("[INFO] No open positions found.")
else:
    for position in positions:
        trader.close_half_position(position)

# Shutdown
trader.shutdown()