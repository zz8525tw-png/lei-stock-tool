import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 頁面設定
st.set_page_config(page_title="雷兄股票分析", layout="wide")

# --- 側邊欄 (維持原本簡約風) ---
with st.sidebar:
    st.header("🔍 搜尋與設定")
    ticker_input = st.text_input("請輸入股票代號", "2330")
    period_choice = st.radio("選擇分析週期", ["日線", "週線", "月線"], index=0)
    submit = st.button("執行全方位分析")
    st.write("---")
    st.write("⚒️ 開發者：[雷兄]")
    st.write("☑️ 不推薦任何投資！")
    st.write("☑️ 祝您投資順利！")

# --- 主程式邏輯 ---
if submit or ticker_input:
    try:
        ticker = ticker_input.upper()
        if not ("." in ticker) and not ticker.isalpha():
            ticker += ".TW"
            
        # 抓取足夠資料計算 60MA
        data = yf.download(ticker, period="1y")
        
        if data.empty:
            st.error("找不到資料")
        else:
            # 指標計算
            data['MA5'] = data['Close'].rolling(window=5).mean()
            data['MA10'] = data['Close'].rolling(window=10).mean()
            data['MA20'] = data['Close'].rolling(window=20).mean()
            data['MA60'] = data['Close'].rolling(window=60).mean()
            
            # KD (9, 3, 3)
            low_9 = data['Low'].rolling(window=9).min()
            high_9 = data['High'].rolling(window=9).max()
            data['RSV'] = 100 * ((data['Close'] - low_9) / (high_9 - low_9))
            data['K'] = data['RSV'].ewm(com=2, adjust=False).mean()
            data['D'] = data['K'].ewm(com=2, adjust=False).mean()
            
            # MACD
            exp1 = data['Close'].ewm(span=12, adjust=False).mean()
            exp2 = data['Close'].ewm(span=26, adjust=False).mean()
            data['MACD'] = exp1 - exp2
            data['Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()
            data['Hist'] = data['MACD'] - data['Signal']

            # --- 頂部數值顯示 (復刻原本風格) ---
            st.title(f"📊 {ticker} 分析 - {period_choice}")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("收盤價", f"{data['Close'].iloc[-1]:.2f}")
            col2.metric("K 值", f"{data['K'].iloc[-1]:.1f}")
            col3.metric("D 值", f"{data['D'].iloc[-1]:.1f}")
            col4.metric("MACD 柱", f"{data['Hist'].iloc[-1]:.2f}")

            # --- 繪圖區 (復刻 K 線 + MA) ---
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                               vertical_spacing=0.1, row_heights=[0.7, 0.3])

            # 主圖：K棒 + 4條均線
            fig.add_trace(go.Candlestick(
                x=data.index, open=data['Open'], high=data['High'],
                low=data['Low'], close=data['Close'], name="K棒",
                increasing_line_color='red', increasing_fillcolor='red',
                decreasing_line_color='green', decreasing_fillcolor='green'
            ), row=1, col=1)
            
            fig.add_trace(go.Scatter(x=data.index, y=data['MA5'], line=dict(color='blue', width=1), name="5MA"), row=1, col=1)
            fig.add_trace(go.Scatter(x=data.index, y=data['MA10'], line=dict(color='orange', width=1), name="10MA"), row=1, col=1)
            fig.add_trace(go.Scatter(x=data.index, y=data['MA20'], line=dict(color='purple', width=1), name="20MA"), row=1, col=1)
            fig.add_trace(go.Scatter(x=data.index, y=data['MA60'], line=dict(color='green', width=1), name="60MA"), row=1, col=1)

            # 下圖：MACD (上紅下綠)
            colors = ['red' if val >= 0 else 'green' for val in data['Hist']]
            fig.add_trace(go.Bar(x=data.index, y=data['Hist'], name="MACD柱", marker_color=colors), row=2, col=1)

            fig.update_layout(height=800, xaxis_rangeslider_visible=False, template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.warning("數據載入中，請點擊「執行全方位分析」或等候 Yahoo 更新。")
