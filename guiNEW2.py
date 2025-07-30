import PySimpleGUI as sg
import random

# Simulated pricing engine (for demonstration purposes)
import threading
import time

# Simulated price updates for live PnL tracking
def simulate_prices(trades, window):
    while True:
        time.sleep(1)
        total_pnl = 0
        updates = []
        for i, trade in enumerate(trades):
            simulated_price = trade['entry'] + random.uniform(-trade['tp'], trade['tp'])
            pnl = (simulated_price - trade['entry']) * trade['direction']
            trade['pnl'] = round(pnl, 2)
            total_pnl += pnl
            updates.append(f"{trade['asset']} | Entry: {trade['entry']} | SL: {trade['sl']} | TP: {trade['tp']} | PnL: {trade['pnl']}")

        window['-TRADELIST-'].update(updates)
        window['-TOTALPNL-'].update(f"Total PnL: {round(total_pnl, 2)}")

# Asset default SL/TP points (can be changed later)
default_settings = {
    'EURUSD': {'sl': 10, 'tp': 20},
    'GBPUSD': {'sl': 12, 'tp': 24},
    'XAUUSD': {'sl': 50, 'tp': 100},
    'SP500': {'sl': 15, 'tp': 30},
    'NAS100': {'sl': 20, 'tp': 40}
}

assets = list(default_settings.keys())
directions = ['Buy', 'Sell']
trades = []

# GUI Layout
layout = [
    [sg.Text("Select Asset:"), sg.Combo(assets, key='-ASSET-', default_value=assets[0])],
    [sg.Text("Direction:"), sg.Combo(directions, key='-DIRECTION-', default_value='Buy')],
    [sg.Text("SL (points):"), sg.Input(key='-SL-', size=(10, 1))],
    [sg.Text("TP (points):"), sg.Input(key='-TP-', size=(10, 1))],
    [sg.Button("Place Trade", bind_return_key=True)],
    [sg.Text("Active Trades:")],
    [sg.Listbox(values=[], size=(60, 10), key='-TRADELIST-', font=('Courier New', 10))],
    [sg.Text("Total PnL:"), sg.Text("0.00", key='-TOTALPNL-', font=('Any', 12), text_color='green')]
]

window = sg.Window("Manual Trade Manager", layout, finalize=True)

# Launch simulated pricing thread
threading.Thread(target=simulate_prices, args=(trades, window), daemon=True).start()

# GUI Event Loop
while True:
    event, values = window.read(timeout=100)

    if event == sg.WINDOW_CLOSED:
        break

    if event == "Place Trade":
        asset = values['-ASSET-']
        direction = 1 if values['-DIRECTION-'] == 'Buy' else -1
        sl = float(values['-SL-']) if values['-SL-'] else default_settings[asset]['sl']
        tp = float(values['-TP-']) if values['-TP-'] else default_settings[asset]['tp']
        entry = round(random.uniform(1.0, 2.0) * 100, 2)  # Simulated price

        trade = {
            'asset': asset,
            'direction': direction,
            'sl': sl,
            'tp': tp,
            'entry': entry,
            'pnl': 0
        }

        trades.append(trade)

window.close()
