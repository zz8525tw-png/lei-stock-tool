import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 頁面設定
st.set_page_config(page_title="雷兄專屬股票分析儀", layout="wide")

# --- 側邊欄配置 ---
with st.sidebar:
    st.header("🔍 搜尋與設定")
    ticker_input = st.text_input("請輸入股票代號 (例: 2330)", "2330")
    period_choice = st.selectbox("選擇分析週期", ["1d", "1m", "3y"], index=0)
    submit = st.button("執行全方位分析")
    st.write("---")
    st.write("⚒️ 開發者：[雷兄]")

# --- 主程式邏輯 ---
if submit or ticker_input:
    try:
        # 自動修正代號
        ticker = ticker_input.upper()
        if not ("." in ticker) and not ticker.isalpha():
            ticker += ".TW"
            
        # 抓取資料
        df = yf.download(ticker, period="1y")
        
        if df.empty:
            st.error("找不到資料，請檢查代號。")
        else:
            # 重設索引確保時間軸正確
            df = df.reset_index()
            
            # --- 技術指標計算 ---
            # 均線 (MA)
            df['MA5'] = df['Close'].rolling(window=5).mean()
            df['MA10'] = df['Close'].rolling(window=10).mean()
            df['MA20'] = df['Close'].rolling(window=20).mean()
            df['MA60'] = df['Close'].rolling(window=60).mean()
            # MACD
            exp1 = df['Close'].ewm(span=12, adjust=False).mean()
            exp2 = df['Close'].ewm(span=26, adjust=False).mean()
            df['MACD'] = exp1 - exp2
            df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
            df['Hist'] = df['MACD'] - df['Signal']
            # KD
            low_9 = df['Low'].rolling(window=9).min()
            high_9 = df['High'].rolling(window=9).max()
            df['RSV'] = 100 * ((df['Close'] - low_9) / (high_9 - low_9))
            df['K'] = df['RSV'].ewm(com=2, adjust=False).mean()
            df['D'] = df['K'].ewm(com=2, adjust=False).mean()

            # --- 頂部摘要區 ---
            st.subheader(f"📊 {ticker} 分析建議")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("當前收盤價", f"{df['Close'].iloc[-1]:.2f}")
            with c2:
                if df['K'].iloc[-1] > df['D'].iloc[-1]:
                    st.success("KD：黃金交叉 (看多)")
                else:
                    st.error("KD：死亡交叉 (看空)")
            with c3:
                if df['Hist'].iloc[-1] > 0:
                    st.success("MACD：柱狀翻紅 (看多)")
                else:
                    st.error("MACD：柱狀翻綠 (看空)")

            # --- 繪圖區 (最重要的修正) ---
            # 建立三層子圖
            fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                               vertical_spacing=0.03, 
                               row_heights=[0.5, 0.25, 0.25])

            # 1. K線圖 + 均線
            fig.add_trace(go.Candlestick(
                x=df['Date'], open=df['Open'], high=df['High'],
                low=df['Low'], close=df['Close'], name="K線",
                increasing_line_color='red', increasing_fillcolor='red',
                decreasing_line_color='green', decreasing_fillcolor='green'
            ), row=1, col=1)
            
            fig.add_trace(go.Scatter(x=df['Date'], y=df['MA5'], line=dict(color='blue', width=1), name="5MA"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df['Date'], y=df['MA20'], line=dict(color='purple', width=1), name="20MA"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df['Date'], y=df['MA60'], line=dict(color='gray', width=1), name="60MA"), row=1, col=1)

            # 2. MACD (上紅下綠)
            colors = ['red' if val >= 0 else 'green' for val in df['Hist']]
            fig.add_trace(go.Bar(x=df['Date'], y=df['Hist'], name="MACD柱", marker_color=colors), row=2, col=1)
            fig.add_trace(go.Scatter(x=df['Date'], y=df['MACD'], line=dict(color='black', width=1), name="DIF"), row=2, col=1)

            # 3. KD
            fig.add_trace(go.Scatter(x=df['Date'], y=df['K'], line=dict(color='blue', width=1.5), name="K"), row=3, col=1)
            fig.add_trace(go.Scatter(x=df['Date'], y=df['D'], line=dict(color='orange', width=1.5), name="D"), row=3, col=1)

            # 版面優化
            fig.update_layout(height=1000, xaxis_rangeslider_visible=False, template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        # 針對 YFRateLimitError 的親切提示
        st.warning("⚠️ 目前 Yahoo 數據庫載入頻率過高，請等候 10 秒後再點擊一次「執行全方位分析」。")

