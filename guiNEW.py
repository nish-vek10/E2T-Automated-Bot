import PySimpleGUI as sg
import MetaTrader5 as mt5
import time

# ------------------------ INIT ------------------------ #
ACCOUNT_BALANCE = 100000        # Starting Capital
MAGIC = 22222                   # Unique identifier for trades sent

# List of tradable symbols and default SL/TP in points
assets_config = {
    "NAS100.i": {"sl_points": 2000, "tp_points": 6000},
    "SP500.i": {"sl_points": 2000, "tp_points": 6000},
    "EURUSD": {"sl_points": 100, "tp_points": 300},
    "XAUUSD": {"sl_points": 300, "tp_points": 900},
    "USDJPY": {"sl_points": 100, "tp_points": 300},
}

directions = ["BUY", "SELL"]
risk_options = ["0.1", "0.25", "0.5", "1.0", "1.5", "2.0"]


# ------------------------ GUI ------------------------ #
# Build the main GUI layout for user to select direction for each asset
layout = [
    [sg.Text("Select Assets, Direction and Risk")],
]

# Add dropdowns for direction and risk for each asset
for asset in assets_config.keys():
    layout.append([
        sg.Text(asset, size=(10, 1)),
        sg.Combo(directions, default_value="BUY", key=f"{asset}_dir", size=(6, 1)),
        sg.Text("Risk %", size=(6, 1)),
        sg.Combo(risk_options, default_value="0.1", key=f"{asset}_risk", size=(5, 1))
    ])

# Adding buttons for user interaction
layout.append([sg.Button("Execute Trades"), sg.Button("Exit")])
window = sg.Window("News-Based Trader", layout)


# ------------------------ MT5 INIT ------------------------ #
if not mt5.initialize():
    sg.popup_error("MT5 initialization failed", mt5.last_error())
    exit()


# ------------------------ TRADE EXECUTION ------------------------ #
# Function to execute trades based on user selections
def execute_trades(user_choices):
    open_trades_info = []

    for symbol, settings in user_choices.items():
        direction = settings["direction"]
        risk_percent = settings["risk"]

        # Determine order type based on chosen direction
        order_type = mt5.ORDER_TYPE_BUY if direction == "BUY" else mt5.ORDER_TYPE_SELL
        sl_points = assets_config[symbol]["sl_points"]
        tp_points = assets_config[symbol]["tp_points"]

        # Getting symbol info and ensuring whether it is available in Market Watch
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None or not symbol_info.visible:
            if not mt5.symbol_select(symbol, True):
                continue    # Skip if unable to add symbol to Market Watch

        # Get latest price info (bid/ask)
        price = mt5.symbol_info_tick(symbol)
        if price is None:
            continue        # Skip if no info available

        # Calculate point value, tick value and risk-based lot size
        point = symbol_info.point
        tick_value = symbol_info.trade_tick_value
        sl_value = sl_points * tick_value
        risk_amount = ACCOUNT_BALANCE * (risk_percent / 100.0)
        lot_size = round(risk_amount / sl_value, 2)     # Risk-based lot sizing

        # Set entry price, SL and TP based on direction
        if order_type == mt5.ORDER_TYPE_BUY:
            entry_price = price.ask
            sl = entry_price - (sl_points * point)
            tp = entry_price + (tp_points * point)
        else:
            entry_price = price.bid
            sl = entry_price + (sl_points * point)
            tp = entry_price - (tp_points * point)

        # Prepare the order request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot_size,
            "type": order_type,
            "price": entry_price,
            "sl": sl,
            "tp": tp,
            "deviation": 10,
            "magic": MAGIC,
            "comment": "News Event Auto Trade",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        # Send the trade request
        result = mt5.order_send(request)

        # If trade was successful, save its details for monitoring
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            open_trades_info.append({
                "symbol": symbol,
                "direction": direction,
                "entry": entry_price,
                "sl": sl,
                "tp": tp,
                "lot": lot_size,
                "ticket": result.order
            })

    return open_trades_info


# ------------------------ LIVE PNL MONITOR ------------------------ #
# Function to display real-time trade PnL updates in a new window
def show_trade_monitor(open_trades):
    layout = [[sg.Text("Live Trade Monitor", font=("Helvetica", 16), justification="center")]]

    # Table Headers
    headings = ["Symbol", "Direction", "Lot Size", "Entry", "SL", "TP", "Running PnL"]
    layout.append([sg.Text(h, size=(12, 1)) for h in headings])

    # Create table rows for each trade
    rows = [[sg.Text("", size=(12, 1), key=f"row_{i}_{j}") for j in range(len(headings))] for i in
            range(len(open_trades))]
    layout.extend(rows)

    # Total Running PnL Display
    layout.append([sg.Text("Running Total PnL:", size=(18, 1)), sg.Text("0.00", key="total_running_pnl", size=(12, 1))])

    # Launch the monitoring window
    monitor_window = sg.Window("Trade Monitor", layout, finalize=True)
    closed_trades = []  # List to store information about trades that have been

    # Start monitoring loop
    while True:
        event, _ = monitor_window.read(timeout=2000)    # Refreshes every 2 seconds
        if event == sg.WINDOW_CLOSED:
            break   # Exit if the monitor window is closed

        total_running_pnl = 0
        all_closed = True  # Flag to check if all trades are closed

        # Loop through each open trade to check status
        for i, trade in enumerate(open_trades):
            pos = mt5.positions_get(ticket=trade["ticket"])  # Get live position info

            if pos:
                # Trade is still open
                pnl = pos[0].profit  # Get current PnL
                total_running_pnl += pnl    # Total running PnL

                # Prepare values to display
                values = [trade["symbol"], trade["direction"], f"{trade['lot']:.2f}", f"{trade['entry']:.2f}",
                          f"{trade['sl']:.2f}", f"{trade['tp']:.2f}", f"{pnl:.2f}"]

                # Update row display for this trade
                for j, val in enumerate(values):
                    monitor_window[f"row_{i}_{j}"].update(val)
                all_closed = False  # At least one trade is still open
            else:
                # Trade is closed (no longer found in live positions)
                if not any(ct["ticket"] == trade["ticket"] for ct in closed_trades):
                    # Retrieve closed deals from account history in the past 24h
                    deal = mt5.history_deals_get(time.time() - 86400, time.time())
                    if deal:
                        for d in deal:
                            # Match by ticket and confirm it’s a closing deal
                            if d.ticket == trade["ticket"] and d.entry == mt5.DEAL_ENTRY_OUT:
                                closed_trade = {
                                    "symbol": trade["symbol"],
                                    "direction": trade["direction"],
                                    "lot": trade["lot"],
                                    "entry": trade["entry"],
                                    "sl": trade["sl"],
                                    "tp": trade["tp"],
                                    "close_price": d.price,
                                    "pnl": d.profit,
                                    "ticket": trade["ticket"]
                                }
                                closed_trades.append(closed_trade)

        # Update total PnL on the monitor
        monitor_window["total_running_pnl"].update(f"{total_running_pnl:.2f}")

        # If all trades are now closed, show the closed trades summary popup
        if all_closed and closed_trades:
            monitor_window.close()
            show_closed_trades(closed_trades)
            break



# ------------------------ CLOSED TRADES HISTORY WINDOW ------------------------ #
def show_closed_trades(closed_trades):
    # Define layout and heading for the closed trades summary popup
    layout = [[sg.Text("Closed Trades Summary", font=("Helvetica", 16))]]

    # Headings for the columns
    headings = ["Symbol", "Direction", "Lot", "Entry", "SL", "TP", "Close Price", "Closed PnL"]
    layout.append([sg.Text(h, size=(12, 1)) for h in headings])

    total_closed_pnl = 0  # To accumulate total profit/loss

    # Build each row with trade details
    for i, trade in enumerate(closed_trades):
        total_closed_pnl += trade["pnl"]
        row = [
            sg.Text(trade["symbol"], size=(12, 1)),
            sg.Text(trade["direction"], size=(12, 1)),
            sg.Text(f"{trade['lot']:.2f}", size=(12, 1)),
            sg.Text(f"{trade['entry']:.2f}", size=(12, 1)),
            sg.Text(f"{trade['sl']:.2f}", size=(12, 1)),
            sg.Text(f"{trade['tp']:.2f}", size=(12, 1)),
            sg.Text(f"{trade['close_price']:.2f}", size=(12, 1)),
            sg.Text(f"{trade['pnl']:.2f}", size=(12, 1)),
        ]
        layout.append(row)  # Add the row to the window layout

    # Add total PnL at the bottom
    layout.append([sg.Text("Total Closed PnL:", size=(18, 1)), sg.Text(f"{total_closed_pnl:.2f}", size=(12, 1))])

    layout.append([sg.Button("Close Summary")])

    # Show window
    summary_window = sg.Window("Closed Trades Summary", layout)
    while True:
        event, _ = summary_window.read()
        if event in (sg.WINDOW_CLOSED, "Close Summary"):
            break
    summary_window.close()


# ------------------------ MAIN LOOP ------------------------ #
# Handle GUI events in the main loop
while True:
    event, values = window.read()
    if event in (sg.WINDOW_CLOSED, "Exit"):
        break
    if event == "Execute Trades":
        # Filter out selections the user actually made
        user_choices = {
            symbol: values[symbol]
            for symbol in assets_config
            if symbol in values and values[symbol] in directions
        }

        for asset in assets_config:
            direction = values[f"{asset}_dir"]
            risk = float(values[f"{asset}_risk"])
            user_choices[asset] = {"direction": direction, "risk": risk}

        open_trades = execute_trades(user_choices)
        if open_trades:
            show_trade_monitor(open_trades)

        # If trades are opened, show monitor
        if open_trades:
            show_trade_monitor(open_trades)
        else:
            sg.popup("No trades were opened. Check symbol availability or market status.")

window.close()
mt5.shutdown()
