import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 頁面設定
st.set_page_config(page_title="專業多週期股票分析儀", layout="wide")

# --- 側邊欄配置 ---
with st.sidebar:
    st.header("🔍 搜尋與設定")
    quick_pick = st.selectbox("熱門標的", ["手動輸入", "2330.TW", "2454.TW", "0050.TW", "NVDA", "AAPL", "TSLA"])
    
    if quick_pick == "手動輸入":
        ticker_input = st.text_input("請輸入股票代號", "2330")
    else:
        ticker_input = quick_pick
        
    period_choice = st.selectbox("選擇分析週期", ["日線", "週線", "月線"], index=0)
    submit = st.button("執行全方位分析")
    
    st.write("---")
    st.write("⚒️ 開發者：[雷兄]")

# --- 主程式邏輯 ---
if submit or ticker_input:
    try:
        ticker = ticker_input.upper()
        if not ("." in ticker) and not ticker.isalpha():
            ticker += ".TW"
            
        data = yf.download(ticker, period="1y")
        
        if data.empty:
            st.error("找不到資料，請檢查代號。")
        else:
            # --- 指標計算 ---
            # 均線
            data['MA5'] = data['Close'].rolling(window=5).mean()
            data['MA10'] = data['Close'].rolling(window=10).mean()
            data['MA20'] = data['Close'].rolling(window=20).mean()
            data['MA60'] = data['Close'].rolling(window=60).mean()
            # MACD
            exp1 = data['Close'].ewm(span=12, adjust=False).mean()
            exp2 = data['Close'].ewm(span=26, adjust=False).mean()
            data['MACD'] = exp1 - exp2
            data['Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()
            data['Hist'] = data['MACD'] - data['Signal']
            # KD
            low_9 = data['Low'].rolling(window=9).min()
            high_9 = data['High'].rolling(window=9).max()
            data['RSV'] = 100 * ((data['Close'] - low_9) / (high_9 - low_9))
            data['K'] = data['RSV'].ewm(com=2, adjust=False).mean()
            data['D'] = data['K'].ewm(com=2, adjust=False).mean()

            # --- 買進賣出自動分析 ---
            last_k = data['K'].iloc[-1]
            last_d = data['D'].iloc[-1]
            last_hist = data['Hist'].iloc[-1]
            
            st.subheader(f"📈 {ticker} 分析建議")
            col1, col2, col3 = st.columns(3)
            with col1:
                if last_k > last_d:
                    st.success("KD 指標：黃金交叉 (偏多)")
                else:
                    st.error("KD 指標：死亡交叉 (偏空)")
            with col2:
                if last_hist > 0:
                    st.success("MACD 指標：柱狀圖翻紅 (偏多)")
                else:
                    st.error("MACD 指標：柱狀圖翻綠 (偏空)")
            with col3:
                price = data['Close'].iloc[-1]
                ma5 = data['MA5'].iloc[-1]
                if price > ma5:
                    st.success("均線狀態：站上 5MA (強勢)")
                else:
                    st.error("均線狀態：跌破 5MA (弱勢)")

            # --- 繪圖區 ---
            fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                               vertical_spacing=0.05, 
                               row_heights=[0.5, 0.25, 0.25])

            # 1. K線圖 + 均線 (核心區)
            fig.add_trace(go.Candlestick(
                x=data.index, open=data['Open'], high=data['High'],
                low=data['Low'], close=data['Close'], name="K線",
                increasing_line_color='red', increasing_fillcolor='red',
                decreasing_line_color='green', decreasing_fillcolor='green'
            ), row=1, col=1)
            
            fig.add_trace(go.Scatter(x=data.index, y=data['MA5'], line=dict(color='blue', width=1), name="5MA"), row=1, col=1)
            fig.add_trace(go.Scatter(x=data.index, y=data['MA10'], line=dict(color='orange', width=1), name="10MA"), row=1, col=1)
            fig.add_trace(go.Scatter(x=data.index, y=data['MA20'], line=dict(color='purple', width=1), name="20MA"), row=1, col=1)
            fig.add_trace(go.Scatter(x=data.index, y=data['MA60'], line=dict(color='gray', width=1), name="60MA"), row=1, col=1)

            # 2. MACD (上紅下綠)
            colors = ['red' if val >= 0 else 'green' for val in data['Hist']]
            fig.add_trace(go.Bar(x=data.index, y=data['Hist'], name="MACD柱", marker_color=colors), row=2, col=1)
            fig.add_trace(go.Scatter(x=data.index, y=data['MACD'], line=dict(color='black', width=1), name="DIF"), row=2, col=1)
            fig.add_trace(go.Scatter(x=data.index, y=data['Signal'], line=dict(color='blue', width=1), name="MACD線"), row=2, col=1)

            # 3. KD
            fig.add_trace(go.Scatter(x=data.index, y=data['K'], line=dict(color='blue', width=1.5), name="K"), row=3, col=1)
            fig.add_trace(go.Scatter(x=data.index, y=data['D'], line=dict(color='orange', width=1.5), name="D"), row=3, col=1)

            fig.update_layout(height=900, xaxis_rangeslider_visible=False, template="plotly_white", showlegend=True)
            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.info("📈 數據載入中，請再次點擊「執行全方位分析」或稍候。")
