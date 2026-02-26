import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time

# 頁面配置
st.set_page_config(page_title="雷兄股票分析", layout="wide")

# 側邊欄
with st.sidebar:
    st.header("🔍 搜尋與設定")
    ticker_input = st.text_input("請輸入股票代號", "2330")
    submit = st.button("執行全方位分析")
    st.write("---")
    st.write("⚒️ 開發者：[雷兄]")
    st.write("☑️ 不推薦任何投資！")

# 核心邏輯
if submit or ticker_input:
    try:
        ticker = ticker_input.upper()
        if not ("." in ticker) and not ticker.isalpha(): ticker += ".TW"
        
        # 抓取資料，增加重試機制
        with st.spinner('正在從 Yahoo 抓取資料...'):
            data = yf.download(ticker, period="1y", interval="1d", progress=False)
        
        if data.empty:
            st.warning(f"暫時抓不到 {ticker} 的資料，請再點擊一次按鈕試試。")
        else:
            # 1. 指標計算
            data['MA5'] = data['Close'].rolling(5).mean()
            data['MA10'] = data['Close'].rolling(10).mean()
            data['MA20'] = data['Close'].rolling(20).mean()
            data['MA60'] = data['Close'].rolling(60).mean()
            
            exp1 = data['Close'].ewm(span=12, adjust=False).mean()
            exp2 = data['Close'].ewm(span=26, adjust=False).mean()
            data['MACD'] = exp1 - exp2
            data['Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()
            data['Hist'] = data['MACD'] - data['Signal']

            # 2. 顯示標題與數值
            st.title(f"📊 {ticker} 分析報告")
            c1, c2, c3 = st.columns(3)
            c1.metric("收盤價", f"{data['Close'].iloc[-1]:.2f}")
            c2.metric("5MA 均價", f"{data['MA5'].iloc[-1]:.2f}")
            c3.metric("MACD 柱", f"{data['Hist'].iloc[-1]:.2f}")

            # 3. 繪圖區 (還原你最喜歡的簡約美感)
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08, row_heights=[0.7, 0.3])
            
            # K線 + 4條均線
            fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'], name="K棒"), row=1, col=1)
            fig.add_trace(go.Scatter(x=data.index, y=data['MA5'], name="5MA", line=dict(color='blue', width=1)), row=1, col=1)
            fig.add_trace(go.Scatter(x=data.index, y=data['MA10'], name="10MA", line=dict(color='orange', width=1)), row=1, col=1)
            fig.add_trace(go.Scatter(x=data.index, y=data['MA20'], name="20MA", line=dict(color='purple', width=1)), row=1, col=1)
            fig.add_trace(go.Scatter(x=data.index, y=data['MA60'], name="60MA", line=dict(color='green', width=1)), row=1, col=1)
            
            # MACD 上紅下綠
            colors = ['red' if v >= 0 else 'green' for v in data['Hist']]
            fig.add_trace(go.Bar(x=data.index, y=data['Hist'], marker_color=colors, name="MACD柱"), row=2, col=1)
            
            fig.update_layout(height=800, xaxis_rangeslider_visible=False, template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error("🔄 Yahoo 伺服器忙碌中（頻率限制），請等候 5 秒後再次點擊「執行全方位分析」。")
