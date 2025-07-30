# pip install zmq
# pip install json

######   B-A-S-E  C-L-A-S-S   ######

# mt4_bridge.py

import zmq
import json

class MT4Bridge:
    def __init__(self, port=5555):
        context = zmq.Context()
        self.socket = context.socket(zmq.PUB)
        self.socket.bind(f"tcp://*:{port}")
        print(f"[INFO] MT4Bridge initialized on port {port}")

    def send_order(self, symbol, order_type, sl_points, risk_percent, comment="PythonTrade"):
        message = {
            "action": "trade",
            "symbol": symbol,
            "order_type": order_type.lower(),  # "buy" or "sell"
            "sl_points": sl_points,
            "risk_percent": risk_percent,
            "comment": comment
        }
        self.socket.send_string(json.dumps(message))
        print(f"[SENT] Trade order → {message}")

    def close_all(self):
        message = {"action": "close_all"}
        self.socket.send_string(json.dumps(message))
        print("[SENT] All Trades Closed!")

    def close_partial(self, symbol, percentage=0.5):
        message = {
            "action": "close_partial",
            "symbol": symbol,
            "percentage": percentage
        }
        self.socket.send_string(json.dumps(message))
        print(f"[SENT] Close partial → {symbol} ({percentage*100}%)")
