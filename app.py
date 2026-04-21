import os
os.system("pip install plotly scikit-learn")

import streamlit as st
import requests
import pandas as pd
import numpy as np
import time
import plotly.express as px

# --------------------------
# PAGE CONFIG
# --------------------------
st.set_page_config(page_title="Crypto Analytics Dashboard", layout="wide")

st.title("📊 Real-Time Crypto Analytics Dashboard")

# --------------------------
# SIDEBAR
# --------------------------
st.sidebar.header("⚙️ Settings")

coin = st.sidebar.selectbox(
    "Select Cryptocurrency",
    ["bitcoin", "ethereum", "dogecoin", "litecoin", "solana"]
)

refresh_rate = st.sidebar.slider("Auto Refresh (sec)", 10, 120, 30)

alert_price = st.sidebar.number_input("🔔 Alert Price", value=0.0)

# --------------------------
# CACHE FUNCTION
# --------------------------
@st.cache_data(ttl=30)
def fetch_data(url):
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None

# --------------------------
# RSI FUNCTION
# --------------------------
def compute_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# --------------------------
# FETCH DATA
# --------------------------
st.subheader(f"📈 Analysis for {coin.upper()}")

url = f"https://api.coingecko.com/api/v3/coins/{coin}/market_chart?vs_currency=usd&days=30"
data = fetch_data(url)

if data and "prices" in data:

    df = pd.DataFrame(data["prices"], columns=["Time", "Price"])
    df["Time"] = pd.to_datetime(df["Time"], unit="ms")
    df.set_index("Time", inplace=True)

    # --------------------------
    # FEATURE ENGINEERING
    # --------------------------
    df["returns"] = df["Price"].pct_change()

    df["MA_7"] = df["Price"].rolling(7).mean()
    df["MA_14"] = df["Price"].rolling(14).mean()

    df["RSI"] = compute_rsi(df["Price"])

    volatility = df["returns"].std()

    latest = df.iloc[-1]

    # --------------------------
    # METRICS
    # --------------------------
    col1, col2, col3 = st.columns(3)

    col1.metric("💰 Current Price", f"${latest['Price']:.2f}")
    col2.metric("📊 Volatility", f"{volatility:.5f}")
    col3.metric("📉 RSI", f"{latest['RSI']:.2f}")

    # --------------------------
    # ALERT SYSTEM
    # --------------------------
    if alert_price > 0:
        if latest["Price"] >= alert_price:
            st.success(f"🚨 Alert: Price crossed ${alert_price}")
        else:
            st.info(f"Waiting for price to reach ${alert_price}")

    # --------------------------
    # PRICE + MOVING AVERAGE
    # --------------------------
    st.subheader("📊 Price & Moving Averages")

    fig = px.line(df, y=["Price", "MA_7", "MA_14"],
                  title="Price with Moving Averages")

    st.plotly_chart(fig, use_container_width=True)

    # --------------------------
    # RSI CHART
    # --------------------------
    st.subheader("📉 RSI Indicator")

    fig_rsi = px.line(df, y="RSI", title="Relative Strength Index")
    st.plotly_chart(fig_rsi, use_container_width=True)

    # --------------------------
    # TRADING SIGNALS
    # --------------------------
    st.subheader("📢 Trading Signals")

    if latest["MA_7"] > latest["MA_14"]:
        st.success("📈 Bullish Trend (Buy Signal)")
    else:
        st.error("📉 Bearish Trend (Sell Signal)")

    if latest["RSI"] > 70:
        st.warning("⚠️ Overbought → Possible Correction")
    elif latest["RSI"] < 30:
        st.info("🟢 Oversold → Possible Bounce")

    # --------------------------
    # RISK ANALYSIS
    # --------------------------
    st.subheader("📊 Risk Analysis")

    st.metric("Volatility (Std Dev of Returns)", f"{volatility:.5f}")

    # --------------------------
    # INSIGHTS ENGINE
    # --------------------------
    st.subheader("📌 Key Insights")

    if latest["MA_7"] > latest["MA_14"]:
        st.write("• Short-term trend is stronger → bullish momentum")
    else:
        st.write("• Long-term trend dominates → bearish pressure")

    st.write(f"• Volatility level indicates risk at {volatility:.5f}")

    if latest["RSI"] > 70:
        st.write("• Asset may be overbought → correction likely")
    elif latest["RSI"] < 30:
        st.write("• Asset may be oversold → potential opportunity")

else:
    st.error("❌ Failed to fetch data")

# --------------------------
# AUTO REFRESH
# --------------------------
st.caption(f"Refreshing every {refresh_rate} seconds...")
time.sleep(refresh_rate)
st.rerun()
