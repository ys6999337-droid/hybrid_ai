import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="FRIDAY UNIFIED AI", layout="wide")

# --- STYLE ---
st.markdown("""
    <style>
    .main { background-color: #0d1117; color: white; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    .stButton>button { width: 100%; border-radius: 20px; background: linear-gradient(45deg, #00c6ff, #0072ff); color: white; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

class FridayAI:
    @staticmethod
    def get_data(symbol, interval, period="1mo"):
        try:
            df = yf.download(symbol, period=period, interval=interval, progress=False)
            return df
        except:
            return pd.DataFrame()

    @staticmethod
    def apply_brain(df):
        # Trend & Momentum Indicators
        df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        df['RSI'] = 100 - (100 / (1 + (gain/loss)))
        
        # Bollinger Bands
        df['MA20'] = df['Close'].rolling(20).mean()
        df['STD'] = df['Close'].rolling(20).std()
        df['Upper_BB'] = df['MA20'] + (df['STD'] * 2)
        df['Lower_BB'] = df['MA20'] - (df['STD'] * 2)
        
        # Fibonacci
        high_50 = df['High'].tail(50).max()
        low_50 = df['Low'].tail(50).min()
        df['Fib_618'] = high_50 - (0.618 * (high_50 - low_50))
        
        return df

    @staticmethod
    def detect_patterns(df):
        last = df.iloc[-1]
        body = abs(last['Close'] - last['Open'])
        lower_shadow = last['Open'] - last['Low'] if last['Close'] > last['Open'] else last['Close'] - last['Low']
        # Hammer check
        return lower_shadow > (2 * body)

# --- APP UI ---
def main():
    st.title("🤖 FRIDAY UNIFIED AI")
    st.write("Scalping | Swing | Fibonacci | Risk Management")

    # Sidebar Control
    st.sidebar.header("Brain Settings")
    symbol = st.sidebar.text_input("Enter Symbol", "RELIANCE.NS")
    timeframe = st.sidebar.selectbox("Timeframe", ["5m", "15m", "1h", "1d"], index=1)
    risk_amt = st.sidebar.number_input("Risk Per Trade (₹)", 500)

    # Initialize df to avoid NameError
    df = pd.DataFrame()

    if st.button("🚀 EXECUTE AI SCAN"):
        with st.spinner("Analyzing Market..."):
            df = FridayAI.get_data(symbol, timeframe)

        if not df.empty:
            df = FridayAI.apply_brain(df)
            last = df.iloc[-1]
            price = last['Close']

            # Price Check logic
            display_price = f"₹{price:.2f}" if not pd.isna(price) else "N/A"
            display_rsi = f"{last['RSI']:.1f}" if 'RSI' in last and not pd.isna(last['RSI']) else "N/A"

            # Metrics Row
            m1, m2, m3 = st.columns(3)
            m1.metric("Current Price", display_price)
            m2.metric("RSI (Momentum)", display_rsi)

            # Trend logic
            trend_status = "NEUTRAL"
            if not pd.isna(price) and 'EMA_200' in last and not pd.isna(last['EMA_200']):
                trend_status = "BULLISH" if price > last['EMA_200'] else "BEARISH"
            m3.metric("Trend (EMA 200)", trend_status)

            st.divider()

            # Chart and Patterns
            is_hammer = FridayAI.detect_patterns(df)
            fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
            fig.add_trace(go.Scatter(x=df.index, y=df['EMA_200'], name='EMA_200'))
            fig.update_layout(template="plotly_dark", height=450)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("Data fetch failed. Please check symbol.")

if __name__ == "__main__":
    main()

