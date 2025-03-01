#!/usr/bin/env python
# coding: utf-8

# In[1]:


import requests
import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf
from datetime import datetime


# 1. Lấy giá coin hiện tại từ Binance
def fetch_current_price(symbol):
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}USDT"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return float(data['price'])
    else:
        print(f"Không thể lấy giá {symbol} hiện tại.")
        return None


# 2. Lấy dữ liệu lịch sử giá coin với số ngày
def fetch_historical_data(symbol, days=100):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}USDT&interval=1d&limit={days}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        dates = [datetime.fromtimestamp(item[0] / 1000) for item in data]
        open_prices = [float(item[1]) for item in data]
        high_prices = [float(item[2]) for item in data]
        low_prices = [float(item[3]) for item in data]
        close_prices = [float(item[4]) for item in data]
        volumes = [float(item[5]) for item in data]
        return pd.DataFrame({
            "Date": dates,
            "Open": open_prices,
            "High": high_prices,
            "Low": low_prices,
            "Close": close_prices,
            "Volume": volumes
        })
    else:
        print(f"Không thể lấy dữ liệu lịch sử cho {symbol}.")
        return None


# 3. Tính toán RSI
def calculate_rsi(df, period=14):
    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))
    return df


# 4. Tính các đường trung bình động SMA và EMA để phân tích xu hướng
def calculate_moving_averages(df, short_window=20, long_window=50):
    df["SMA_short"] = df["Close"].rolling(window=short_window).mean()
    df["SMA_long"] = df["Close"].rolling(window=long_window).mean()
    df["EMA_short"] = df["Close"].ewm(span=short_window, adjust=False).mean()
    df["EMA_long"] = df["Close"].ewm(span=long_window, adjust=False).mean()
    return df


# 5. Tính MACD
def calculate_macd(df, short_span=12, long_span=26, signal_span=9):
    df["MACD"] = df["Close"].ewm(span=short_span, adjust=False).mean() - df["Close"].ewm(span=long_span,
                                                                                         adjust=False).mean()
    df["MACD_signal"] = df["MACD"].ewm(span=signal_span, adjust=False).mean()
    return df


# 6. Phân tích tín hiệu từ RSI, SMA/EMA và MACD và tính tỷ lệ phần trăm mua/bán
def analyze_signals(df):
    # Phân tích tín hiệu RSI
    latest_rsi = df["RSI"].iloc[-1]
    rsi_signal = "Trung lập"
    rsi_weight = 0
    if latest_rsi < 30:
        rsi_signal = "Mua (Quá bán)"
        rsi_weight = 1  # Tín hiệu mua có trọng số 1
    elif latest_rsi > 70:
        rsi_signal = "Bán (Quá mua)"
        rsi_weight = -1  # Tín hiệu bán có trọng số -1

    # Phân tích tín hiệu SMA
    sma_signal = "Trung lập"
    sma_weight = 0
    if df["SMA_short"].iloc[-1] > df["SMA_long"].iloc[-1]:
        sma_signal = "Mua (Golden Cross)"
        sma_weight = 1
    elif df["SMA_short"].iloc[-1] < df["SMA_long"].iloc[-1]:
        sma_signal = "Bán (Death Cross)"
        sma_weight = -1

    # Phân tích tín hiệu MACD
    macd_signal = "Trung lập"
    macd_weight = 0
    if df["MACD"].iloc[-1] > df["MACD_signal"].iloc[-1]:
        macd_signal = "Mua (MACD cắt trên Signal)"
        macd_weight = 1
    elif df["MACD"].iloc[-1] < df["MACD_signal"].iloc[-1]:
        macd_signal = "Bán (MACD cắt dưới Signal)"
        macd_weight = -1

    # Tổng hợp tín hiệu và tính tỷ lệ % mua và bán
    signals = [rsi_weight, sma_weight, macd_weight]
    buy_percentage = signals.count(1) * 33.33
    sell_percentage = signals.count(-1) * 33.33

    print(f"Tín hiệu RSI: {rsi_signal}")
    print(f"Tín hiệu SMA: {sma_signal}")
    print(f"Tín hiệu MACD: {macd_signal}")
    print(f"% Mua trên thị trường: {buy_percentage:.2f}%")
    print(f"% Bán trên thị trường: {sell_percentage:.2f}%")

    # Lời khuyên
    advice = "Nên MUA" if buy_percentage > sell_percentage else "Nên BÁN"
    print(f"Lời khuyên: {advice}")


# 7. Vẽ biểu đồ nến (Candlestick) và thêm các chỉ báo (RSI, SMA, EMA, MACD)
def plot_data(df, symbol):
    # Biểu đồ nến (candlestick)
    df.set_index('Date', inplace=True)

    # Đường gạch hiển thị giá đóng cửa gần nhất
    last_close = df['Close'].iloc[-1]
    price_line = mpf.make_addplot([last_close] * len(df), color='yellow', linestyle='--', width=1)

    # Cấu hình style cho biểu đồ nến
    sma_short = mpf.make_addplot(df["SMA_short"], color='blue', width=1)
    sma_long = mpf.make_addplot(df["SMA_long"], color='red', width=1)
    ema_short = mpf.make_addplot(df["EMA_short"], color='green', width=1)
    ema_long = mpf.make_addplot(df["EMA_long"], color='orange', width=1)
    macd = mpf.make_addplot(df["MACD"], panel=1, color='purple', secondary_y=False)
    macd_signal = mpf.make_addplot(df["MACD_signal"], panel=1, color='red', secondary_y=False)
    rsi = mpf.make_addplot(df["RSI"], panel=2, color='magenta', secondary_y=False)

    # Biểu đồ nến với các chỉ báo và subplots cho MACD và RSI
    mpf.plot(df, type='candle', style='charles',
             title=f"Biểu đồ nến {symbol}",
             ylabel='Giá (USD)', volume=True, figsize=(14, 8),
             addplot=[sma_short, sma_long, ema_short, ema_long, macd, macd_signal, rsi, price_line])


# 8. Hiển thị các chỉ báo và tín hiệu trong thời gian thực
def display_realtime_analysis(symbol, current_price, df):
    print(f"\nPhân tích {symbol} vào thời điểm {df['Date'].iloc[-1]}:")

    # Tính toán các chỉ báo kỹ thuật (RSI, SMA, EMA, MACD)
    df = calculate_rsi(df)
    df = calculate_moving_averages(df)
    df = calculate_macd(df)

    # Phân tích tín hiệu
    analyze_signals(df)

    # Hiển thị giá hiện tại và các chỉ báo trên đồ thị
    print(f"Giá hiện tại {symbol}: ${current_price:.2f}")

    # Vẽ biểu đồ cho biểu đồ nến và volume cùng với các chỉ báo
    plot_data(df, symbol)


# Hàm chính cập nhật cho phần phân tích theo thời gian thực
def main():
    symbols = {"1": "BTC", "2": "ETH", "3": "SOL", "4": "BNB"}
    print("Chọn coin muốn phân tích:")
    for key, sym in symbols.items():
        print(f"{key}: {sym}")

    choice = input("Nhập số tương ứng với coin muốn phân tích (1-4): ")
    symbol = symbols.get(choice)
    if not symbol:
        print("Lựa chọn không hợp lệ.")
        return

    current_price = fetch_current_price(symbol)
    if current_price:
        print(f"Giá {symbol} hiện tại: ${current_price:.2f}")

    try:
        days = int(input("Nhập số ngày muốn phân tích dữ liệu giá (ví dụ: 50, 100, 200): "))
        if days < 50:
            print("Vui lòng nhập ít nhất 50 ngày để phân tích đủ dữ liệu.")
            return
    except ValueError:
        print("Vui lòng nhập một số nguyên hợp lệ.")
        return

    # Lấy dữ liệu lịch sử cho coin đã chọn
    df = fetch_historical_data(symbol, days)
    if df is not None:
        # Phân tích theo thời gian thực
        display_realtime_analysis(symbol, current_price, df)


if __name__ == "__main__":
    main()

# In[ ]:




