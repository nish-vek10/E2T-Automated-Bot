import yfinance as yf               # For stock data
import pandas as pd                 # For data manipulation
import numpy as np                  # For numerical operations
import matplotlib.pyplot as plt     # For visualizations

# Define parameters
ticker = input("Enter ticker symbol (e.g., AAPL, BTC-USD, TSLA): ").upper() # Chosen Ticker
start_date = "2020-06-01"   # YYYY-MM-DD
end_date = "2025-06-01"     # YYYY-MM-DD
initial_capital = 1000000   # Account size
risk_reward_ratio = 3       # R:R Ratio
lookback = 10               # Candles to look back for swing high/low

# Fetch historical stock data
data = yf.download(ticker, start=start_date, end=end_date, interval="1d", auto_adjust=True)

# Fix: Flatten columns (handles multi-index from yfinance)
if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.get_level_values(0)

# Display first few rows
print(data)

# Compute EMAs
data['EMA20'] = data['Close'].ewm(span=20, adjust=False).mean()
data['EMA100'] = data['Close'].ewm(span=100, adjust=False).mean()

# Helper: Find recent swing highs/lows
def get_swing_low(series):
    return series.min()

def get_swing_high(series):
    return series.max()

# Initialize trade variables
in_position = False
position_type = None
entry_price = sl = tp = 0
capital = initial_capital
trades = []

# Backtest Loop
for i in range(lookback + 1, len(data)):
    # Extract current and previous values as scalars using iloc
    close = data['Close'].iloc[i]
    open_ = data['Open'].iloc[i]
    low = data['Low'].iloc[i]
    high = data['High'].iloc[i]
    ema20 = data['EMA20'].iloc[i]
    ema100 = data['EMA100'].iloc[i]

    prev_ema20 = data['EMA20'].iloc[i - 1]
    prev_ema100 = data['EMA100'].iloc[i - 1]

    # Signals only if no open position
    if not in_position:
        # Buy Signal
        if (
            prev_ema20 > prev_ema100 and
            ema20 > ema100 and
            abs(close - ema20) / ema20 < 0.01 and
            close > open_  # Bullish candle
        ):
            swing_low = get_swing_low(data['Low'].iloc[i - lookback:i])
            sl = swing_low
            entry_price = close
            tp = entry_price + risk_reward_ratio * (entry_price - sl)
            in_position = True
            position_type = 'long'
            entry_date = data.index[i]
            continue

        # Sell Signal
        if (
            prev_ema20 < prev_ema100 and
            ema20 < ema100 and
            abs(close - ema100) / ema100 < 0.01 and
            close < open_  # Bearish candle
        ):
            swing_high = get_swing_high(data['High'].iloc[i - lookback:i])
            sl = swing_high
            entry_price = close
            tp = entry_price - risk_reward_ratio * (sl - entry_price)
            in_position = True
            position_type = 'short'
            entry_date = data.index[i]
            continue

    else:
        # Long Position Management
        if position_type == 'long':
            if low <= sl:
                pnl = sl - entry_price
                trades.append({'Date': data.index[i], 'Type': 'Long SL', 'PnL': pnl})
                in_position = False
            elif high >= tp:
                pnl = tp - entry_price
                trades.append({'Date': data.index[i], 'Type': 'Long TP', 'PnL': pnl})
                in_position = False

        # Short Position Management
        elif position_type == 'short':
            if high >= sl:
                pnl = entry_price - sl
                trades.append({'Date': data.index[i], 'Type': 'Short SL', 'PnL': pnl})
                in_position = False
            elif low <= tp:
                pnl = entry_price - tp
                trades.append({'Date': data.index[i], 'Type': 'Short TP', 'PnL': pnl})
                in_position = False

# Convert trade log to DataFrame
trade_log = pd.DataFrame(trades)
total_profit = trade_log['PnL'].sum()
final_value = initial_capital + total_profit

# Results
print("\n--- Trade Summary ---")
print(trade_log)
print(f"\nIntial Capital:   ${initial_capital:,.2f}")
print(f"Final Capital:      ${final_value:,.2f}")
print(f"Net PnL:            ${total_profit:,.2f}")
print(f"Total Trades:       {len(trade_log)}")
if len(trade_log) > 0:
    win_rate = (trade_log['PnL'] > 0).sum() / len(trade_log)
    print(f"Win Rate:        {win_rate:.2%}")
else:
    print("No trades executed.")

# Plot price and EMAs
plt.figure(figsize=(14, 7))
plt.plot(data['Close'], label='Close', alpha=0.6)
plt.plot(data['EMA20'], label='EMA 20')
plt.plot(data['EMA100'], label='EMA 100')
plt.title(f"{ticker} Price with EMA20 & EMA100")
plt.legend()
plt.grid(True)
plt.show()
