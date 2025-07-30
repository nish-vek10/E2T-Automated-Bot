import MetaTrader5 as mt5
import time
from obsws_python import OBSWS, requests

# === Settings === #
OBS_HOST = "localhost"
OBS_PORT = 4455
OBS_PASSWORD = "1234"

SCENE_FLAT = "flat position"        # When net pnl = 0 or no trades
SCENE_GREEN = "layout winning"      # When net pnl > 0
SCENE_RED = "layout loosing"        # When net pnl < 0
CHECK_INTERVAL = 5  # seconds

# === Connect to MT5 === #
if not mt5.initialize():
    print("MT5 initialize() failed", mt5.last_error())
    quit()

# === Connect to OBS === #
ws = OBSWS(OBS_HOST, OBS_PORT, OBS_PASSWORD)
ws.connect()

def get_net_pnl():
    positions = mt5.positions_get()
    if positions is None or len(positions) == 0:
        return None # no trades
    return sum(pos.profit for pos in positions)

def get_current_scene():
    return ws.call(requests.GetCurrentProgramScene()).getName()

try:
    while True:
        pnl = get_net_pnl()
        current_scene = get_current_scene()

        if pnl is None or abs(pnl) < 0.0001:  # No trades or effectively zero PnL
            if current_scene != SCENE_FLAT:
                ws.call(requests.SetCurrentProgramScene(SCENE_FLAT))
                print("Switched to FLAT scene (no trades or 0 pnl)")
        elif pnl > 0:
            if current_scene != SCENE_GREEN:
                ws.call(requests.SetCurrentProgramScene(SCENE_GREEN))
                print(f"Switched to GREEN scene: PnL = {pnl}")
        elif pnl < 0:
            if current_scene != SCENE_RED:
                ws.call(requests.SetCurrentProgramScene(SCENE_RED))
                print(f"Switched to RED scene: PnL = {pnl}")

        time.sleep(CHECK_INTERVAL)

except KeyboardInterrupt:
    print("Script terminated by user")

finally:
    mt5.shutdown()
    ws.disconnect()
