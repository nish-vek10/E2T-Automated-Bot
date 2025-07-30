import MetaTrader5 as mt5
import pandas as pd
import time
import mplfinance as mpf
import streamlit as st
from datetime import datetime
import matplotlib.pyplot as plt
from streamlit_autorefresh import st_autorefresh

# === STREAMLIT PAGE SETUP ===
st.set_page_config(page_title="XAUUSD MT5 Heikin-Ashi Bot Dashboard", layout="wide")
st.title("📈 XAUUSD Heikin-Ashi Strategy Dashboard")

# === CONNECT TO MT5 === #
if not mt5.initialize():
    st.error(f"MT5 initialization failed: {mt5.last_error()}")
    st.stop()

account = mt5.account_info()
if account is None:
    st.error(f"Failed to retrieve account info: {mt5.last_error()}")
    mt5.shutdown()
    st.stop()

initial_cap = account.balance
print(f"✅ MT5 Account Connected! \nAccount: {account.login}, \nBalance: {initial_cap:.2f}\n")

# === PARAMETERS === #
symbol = "XAUUSD"
timeframe = mt5.TIMEFRAME_M5    # 5-minute candles
lot_size = 0.1                  # constant lot size per trade

# === PLACE ORDER WITHOUT SL/TP === #
def place_trade(direction):
    """
    Executes a market buy/sell order without SL or TP.
    """
    tick = mt5.symbol_info_tick(symbol)
    price = tick.ask if direction == "buy" else tick.bid
    order_type = mt5.ORDER_TYPE_BUY if direction == "buy" else mt5.ORDER_TYPE_SELL

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot_size,
        "type": order_type,
        "price": price,
        "deviation": 5,
        "magic": 123456,
        "comment": f"{direction.upper()} trade from bot",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"❌ Trade failed: {result.retcode}")
    else:
        print(f"✅ {direction.upper()} trade executed at {price}")

# === CLOSE OPPOSITE ORDERS BEFORE NEW ENTRY === #
def close_existing(direction):
    """
    Closes any open trade in the opposite direction before entering a new one.
    """
    opposite_type = mt5.ORDER_TYPE_SELL if direction == "buy" else mt5.ORDER_TYPE_BUY
    positions = mt5.positions_get(symbol=symbol)
    if positions:
        for pos in positions:
            if pos.type == opposite_type:
                price = mt5.symbol_info_tick(symbol).bid if pos.type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(symbol).ask
                close_request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": symbol,
                    "volume": pos.volume,
                    "type": mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY,
                    "position": pos.ticket,
                    "price": price,
                    "deviation": 5,
                    "magic": 123456,
                    "comment": "Closing opposite trade",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC,
                }
                result = mt5.order_send(close_request)
                if result.retcode == mt5.TRADE_RETCODE_DONE:
                    print(f"✅ Closed opposite trade: ticket {pos.ticket}")
                else:
                    print(f"❌ Failed to close trade: {result.retcode}")


# === HEIKIN-ASHI CANDLE CALCULATION === #
def calculate_heikin_ashi(df):
    """
    Converts OHLC candles into Heikin-Ashi format.
    """
    ha_df = pd.DataFrame(index=df.index)
    ha_df['ha_close'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4

    ha_open = [(df['open'].iloc[0] + df['close'].iloc[0]) / 2]
    for i in range(1, len(df)):
        ha_open.append((ha_open[i - 1] + ha_df['ha_close'].iloc[i - 1]) / 2)

    ha_df['ha_open'] = ha_open
    ha_df['ha_high'] = df[['high', 'low', 'close']].max(axis=1)
    ha_df['ha_low'] = df[['high', 'low', 'close']].min(axis=1)

    return ha_df

# === FETCH DATA, RUN STRATEGY, RETURN SIGNAL AND PLOT === #
def run_strategy_and_plot():
    """
    Core loop: fetch data, calculate signals, plot chart, and trade.
    """
    bars = mt5.copy_rates_from_pos(symbol, timeframe, 0, 500) # Fetch latest 500 bars
    if bars is None:
        print("❌ Failed to fetch bars:", mt5.last_error())
        return

    df = pd.DataFrame(bars)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=True)

    # Calculate Heikin-Ashi candles
    ha_df = calculate_heikin_ashi(df)
    print(ha_df.tail(10))  # preview last few Heikin Ashi candles

    # Chandelier Exit Indicator Logic
    atr_period = 1
    atr_mult = 1.85

    tr = pd.DataFrame(index=ha_df.index)
    tr['tr'] = pd.concat([
            ha_df['ha_high'] - ha_df['ha_low'],
            abs(ha_df['ha_high'] - ha_df['ha_close'].shift()),
            abs(ha_df['ha_low'] - ha_df['ha_close'].shift())
        ], axis=1).max(axis=1)

    atr = tr['tr'].rolling(window=atr_period).mean()
    upper = ha_df['ha_high'].rolling(window=atr_period).max() - atr_mult * atr
    lower = ha_df['ha_low'].rolling(window=atr_period).min() + atr_mult * atr

    # Trend direction based on Chandelier levels
    trend = [0]
    for i in range(1, len(ha_df)):
        if ha_df['ha_close'].iloc[i] > upper.iloc[i - 1]:
            trend.append(1)
        elif ha_df['ha_close'].iloc[i] < lower.iloc[i - 1]:
            trend.append(-1)
        else:
            trend.append(trend[i - 1])

    # Add trend and signal columns
    ha_df['trend'] = trend
    ha_df['buy_signal'] = (ha_df['trend'] == 1) & (pd.Series(trend).shift() == -1)
    ha_df['sell_signal'] = (ha_df['trend'] == -1) & (pd.Series(trend).shift() == 1)

    # Get recent signal
    recent = ha_df.iloc[-1]
    if recent['buy_signal']:
        signal = "BUY"
    elif recent['sell_signal']:
        signal = "SELL"
    else:
        signal = "NO SIGNAL"

    if recent['buy_signal']:
        print(f"\n⬆️ BUY signal at {recent.name}")
    elif recent['sell_signal']:
        print(f"\n🔻 SELL signal at {recent.name}")
    else:
        print(f"\n⏳ No signal at {recent.name}")

    # === PLOT THE CHART WITH SIGNALS === #
    ha_plot_df = ha_df.rename(columns={
        'ha_open': 'Open',
        'ha_high': 'High',
        'ha_low': 'Low',
        'ha_close': 'Close'
    })[['Open', 'High', 'Low', 'Close']]

    # Add buy/sell markers
    addplots = []
    buys = ha_df[ha_df['buy_signal']]
    if not buys.empty:
        addplots.append(mpf.make_addplot(buys['ha_low'] - 1, type='scatter', marker='^', color='green', markersize=80))
    sells = ha_df[ha_df['sell_signal']]
    if not sells.empty:
        addplots.append(mpf.make_addplot(sells['ha_high'] + 1, type='scatter', marker='v', color='red', markersize=80))

    # Create mplfinance plot object (figure)
    fig, axlist = mpf.plot(
        ha_plot_df[-100:], type='candle', style='yahoo', addplot=addplots,
        title=f"{symbol} Heikin-Ashi Strategy", ylabel="Price", volume=False,
        returnfig=True, figratio=(12, 6), figscale=1.2
    )

    return signal, fig, ha_df

# === DISPLAY OPEN POSITIONS === #
def get_open_positions_summary():
    positions = mt5.positions_get(symbol=symbol)
    if not positions:
        return "No open positions."

    pos_summary = ""
    for pos in positions:
        type_str = "BUY" if pos.type == mt5.ORDER_TYPE_BUY else "SELL"
        pos_summary += f"Ticket: {pos.ticket}, Type: {type_str}, Volume: {pos.volume}, Price: {pos.price_open:.2f}\n"

    return pos_summary

# === MAIN APP LOOP === #
def main():
    # Show initial account balance
    account_info = mt5.account_info()
    st.sidebar.markdown(f"### Account Balance: ${account_info.balance:.2f}")

    # Button to manually run one iteration
    if st.sidebar.button("Run Strategy Now"):
        signal, fig, ha_df = run_strategy_and_plot()
        if signal is not None:
            st.sidebar.markdown(f"### Latest Signal: {signal}")

            if signal == "BUY":
                close_existing("buy")
                place_trade("buy")
            elif signal == "SELL":
                close_existing("sell")
                place_trade("sell")

            # Show positions
            positions_summary = get_open_positions_summary()
            st.sidebar.text_area("Open Positions:", positions_summary, height=150)

            # Show plot
            st.pyplot(fig)
        else:
            st.error("Could not run strategy.")

    # Auto refresh every 5 minutes
    refresh_rate_sec = 5 * 60
    st.markdown(f"⏳ Auto-refreshes every {refresh_rate_sec//60} minutes.")

    # Run once on load and then auto-refresh with Streamlit's built-in rerun
    signal, fig, ha_df = run_strategy_and_plot()
    if signal is not None:
        st.markdown(f"### Latest Signal: {signal}")

        if signal == "BUY":
            close_existing("buy")
            place_trade("buy")
        elif signal == "SELL":
            close_existing("sell")
            place_trade("sell")

        positions_summary = get_open_positions_summary()
        st.text_area("Open Positions:", positions_summary, height=150)

        st.pyplot(fig)
    else:
        st.error("Could not run strategy.")

    st_autorefresh(interval=refresh_rate_sec * 1000, key="refresh")

# Run app
try:
    main()
except Exception as e:
    st.error(f"Unexpected error: {e}")
finally:
    mt5.shutdown()