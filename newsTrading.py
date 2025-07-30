#pip install requests

import requests
from datetime import datetime, timedelta
import MetaTrader5 as mt5

# === Your API Key from Financial Modeling Prep ===
API_KEY = 'your_api_key_here'  # Replace with your actual API key

# === Function: Check for upcoming high-impact news events ===
def check_upcoming_news(hours_ahead=1):
    """
    Fetches high-impact economic events from the FMP API within the next `hours_ahead` window.
    Returns a list of high-impact events.
    """
    now = datetime.utcnow()
    end_time = now + timedelta(hours=hours_ahead)

    # Format the API endpoint for the time range
    url = (
        f"https://financialmodelingprep.com/api/v4/economic_calendar?"
        f"from={now.date()}&to={end_time.date()}&apikey={API_KEY}"
    )

    # Make API request
    response = requests.get(url)
    if response.status_code != 200:
        print("[ERROR] Failed to fetch economic calendar.")
        return []

    # Parse and filter high-impact events
    events = response.json()
    filtered_events = []
    for event in events:
        if event.get("importance", "").lower() == "high":
            event_time = datetime.strptime(event["date"], "%Y-%m-%d %H:%M:%S")
            if now <= event_time <= end_time:
                filtered_events.append(event)

    return filtered_events


# === Step 1: Check for high-impact news ===
print("[INFO] Checking for high-impact news before trading...")
news = check_upcoming_news(hours_ahead=1)  # Adjust lookahead window as needed

if news:
    print("[⚠️] High-impact news events detected. Delaying or skipping trades.")
    for n in news:
        print(f" - {n['country']}: {n['event']} at {n['date']} (Impact: {n['importance']})")
else:
    print("[✅] No high-impact news. Proceeding with trade setup...")

    # === Step 2: Initialize MetaTrader 5 connection ===
    if not mt5.initialize():
        raise SystemExit(f"[ERROR] MT5 initialization failed: {mt5.last_error()}")

    # === Step 3: Example Trade (XAUUSD BUY) ===
    symbol = "XAUUSD"
    lot = 0.1
    sl_points = 100
    tp_points = 200

    # Get latest market tick for the symbol
    tick = mt5.symbol_info_tick(symbol)
    if not tick:
        print(f"[ERROR] No market data for {symbol}")
        mt5.shutdown()
        exit()

    # Use ask for BUY, bid for SELL
    price = tick.ask
    symbol_info = mt5.symbol_info(symbol)
    point = symbol_info.point

    # Calculate SL and TP prices
    sl = price - sl_points * point
    tp = price + tp_points * point

    # Construct order request
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": mt5.ORDER_TYPE_BUY,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": 10,
        "magic": 123456,
        "comment": "News-filtered trade",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    # Send trade order
    result = mt5.order_send(request)
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        print(f"[✅] Trade executed: BUY {symbol} at {price:.2f}")
    else:
        print(f"[❌] Trade failed (retcode: {result.retcode})")

    # Shutdown MT5 after trading
    mt5.shutdown()
