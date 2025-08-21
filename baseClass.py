# pip install MetaTrader5
# python -m tkinter
# pip install tkinter
# pip install pygetwindow
# pip install pywinauto

######   B-A-S-E  C-L-A-S-S   ######

import MetaTrader5 as mt5
import time

class MT5Trader:
    MAGIC_NUMBER = 123456 # Unique identifier for this EA (Expert Advisor)

    # Initialize the MT5 terminal connection
    def __init__(self):
        if not mt5.initialize():
            raise SystemExit(f"MT5 initialization failed: {mt5.last_error()}")

    # Shut down the MT5 connection
    def shutdown(self):
        mt5.shutdown()

    # Get the latest tick data and symbol info
    def get_tick_info(self, symbol):
        tick = mt5.symbol_info_tick(symbol)
        symbol_info = mt5.symbol_info(symbol)
        if not tick:
            print(f"[ERROR] No tick data for {symbol}")
            return None, None
        if not symbol_info:
            print(f"[ERROR] No symbol info for {symbol}")
            return None, None
        return tick, symbol_info

    # Ensures SL is not below the broker's minimum stop level
    def adjust_sl_to_broker_min(self, symbol_info, sl_points):
        min_sl = symbol_info.trade_stops_level
        if sl_points < min_sl:
            print(f"[ERROR] {symbol_info.name}: SL too close ({sl_points}). Adjusting to min allowed: {min_sl}")
            return min_sl
        return sl_points

    def _ensure_symbol_ready(self, symbol):
        info = mt5.symbol_info(symbol)
        if info is None:
            print(f"[ERROR] {symbol}: No symbol_info.")
            return None
        if not info.visible:
            mt5.symbol_select(symbol, True)
        return mt5.symbol_info(symbol)  # refresh

    def _wait_fresh_tick(self, symbol, timeout_ms=500):
        """Wait for a fresh tick up to timeout_ms; return tick or None."""
        import time
        start = time.time()
        last_time = 0
        while (time.time() - start) * 1000 < timeout_ms:
            tick = mt5.symbol_info_tick(symbol)
            if tick and tick.time_msc and tick.time_msc != last_time:
                return tick
            last_time = tick.time_msc if tick else last_time
            time.sleep(0.01)  # 10ms
        return mt5.symbol_info_tick(symbol)

    """
            Calculate the lot size based on:
            - Account balance
            - Risk percentage
            - Stop-loss size (in points)
    """
    def calculate_lot_size(self, symbol, sl_points, risk_percent):
        account_info = mt5.account_info()
        if account_info is None:
            print("[ERROR] Unable to retrieve account info.")
            return 0.0

        balance = account_info.balance
        risk_amount = (risk_percent / 100) * balance # Amount to risk per trade

        tick, symbol_info = self.get_tick_info(symbol)
        if not tick or not symbol_info:
            return 0.0

        contract_size = symbol_info.trade_contract_size
        if contract_size == 0 or symbol_info.trade_tick_value == 0:
            print(f"[ERROR] Invalid contract or tick value for {symbol}")
            return 0.0

        point = symbol_info.point
        sl_price_range = sl_points * point
        tick_value = symbol_info.trade_tick_value

        if sl_price_range <= 0 or contract_size <= 0 or tick_value <= 0:
            print(f"[ERROR] Invalid SL or contract parameters for {symbol}")
            return 0.0

        # Simplified lot size formula (approximate): lot = risk / (SL in price * value per lot)
        sl_value_per_lot = sl_price_range * (tick_value / point)
        if sl_value_per_lot == 0:
            print(f"[ERROR] Division by zero for SL value per lot on {symbol}")
            return 0.0

        # Raw lot size
        lot = risk_amount / sl_value_per_lot

        # Enforce allowed lot size constraints
        min_lot = symbol_info.volume_min
        max_lot = symbol_info.volume_max
        lot_step = symbol_info.volume_step

        # Round down to nearest allowed step and limit to allowed range
        lot = max(min_lot, min(lot, max_lot))
        lot = round(lot / lot_step) * lot_step
        lot = round(lot, 2)

        if lot < min_lot:
            print(f"[WARNING] {symbol}: Calculated lot {lot} is below minimum {min_lot}. Skipping trade.")
            return 0.0

        return lot

    """
            Places a market order (BUY/SELL) with SL and comment.
    """
    def place_order(self, symbol, order_type, lot, sl_points, comment="AutoTrade"):
        tick, symbol_info = self.get_tick_info(symbol)
        if not tick or not symbol_info:
            return False

        price = tick.ask if order_type == mt5.ORDER_TYPE_BUY else tick.bid
        point = symbol_info.point

        # Ensure SL respects the broker's minimum stop level
        min_sl_points = symbol_info.trade_stops_level
        if sl_points < min_sl_points:
            print(f"[ERROR] {symbol}: SL too close ({sl_points}). Adjusting to min allowed: {min_sl_points}")
            sl_points = min_sl_points

        # Calculate SL price depending on order direction
        sL = price - (sl_points * point) if order_type == mt5.ORDER_TYPE_BUY else price + (sl_points * point)

        # Construct the trade request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": order_type,
            "price": price,
            "deviation": 250,
            "sl": sL,
            "magic": self.MAGIC_NUMBER,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        # Send the order
        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"[OK] {symbol}: Trade executed successfully.")
            return True
        else:
            print(f"[FAIL] {symbol}: Order failed. Retcode: {result.retcode}")
            print(f"→ Full result: {result}")
            return False

    """
            Closes half of the open position.
    """
    def close_half_position(self, position):
        symbol = position.symbol
        ticket = position.ticket

        # Fetch symbol info to get lot step and min volume
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            print(f"[ERROR] No symbol info for {symbol}")
            return

        half_volume = position.volume / 2
        min_lot = symbol_info.volume_min
        lot_step = symbol_info.volume_step

        # Round volume to nearest lot step
        rounded_volume = round(half_volume / lot_step) * lot_step

        # Ensure volume is valid
        if rounded_volume < min_lot:
            print(f"[SKIPPED] {symbol} 50% volume ({rounded_volume}) < min lot size ({min_lot})")
            return

        # Determine close direction (opposite of position type)
        order_type = mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY

        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            print(f"[ERROR] No tick data for {symbol}")
            return

        price = tick.bid if order_type == mt5.ORDER_TYPE_SELL else tick.ask

        # Create request to close partial position
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": rounded_volume,
            "type": order_type,
            "position": ticket,
            "price": price,
            "deviation": 250,
            "magic": self.MAGIC_NUMBER,
            "comment": "PartialClose50",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        # Send request
        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"Closed 50% of {symbol} position #{ticket}")
        else:
            print(f"Failed to close 50% of {symbol} position #{ticket} (retcode: {result.retcode})")

    """
            Closes all open positions in the account.
    """
    def close_all_positions(self):
        positions = mt5.positions_get()
        if not positions:
            print("[INFO] No open positions.")
            return

        for pos in positions:
            symbol = pos.symbol
            ticket = pos.ticket
            volume = pos.volume

            # Determine opposite order type to close position
            order_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY

            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                print(f"[ERROR] No tick data for {symbol}")
                continue

            price = tick.bid if order_type == mt5.ORDER_TYPE_SELL else tick.ask

            # Create close request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": order_type,
                "position": ticket,
                "price": price,
                "deviation": 250,
                "magic": self.MAGIC_NUMBER,
                "comment": "CloseAllScript",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            # Send the close order
            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"[OK] Closed {symbol} position #{ticket} at price {price}")
            else:
                print(f"[FAIL] Could not close {symbol} position #{ticket} (retcode: {result.retcode})")
