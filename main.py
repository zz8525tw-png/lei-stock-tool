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
    st.write("投資有賺有賠")
    st.write("風險自負")

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
            # --- 技術指標計算 ---
            # 1. 均線 MA
            data['MA5'] = data['Close'].rolling(window=5).mean()
            data['MA10'] = data['Close'].rolling(window=10).mean()
            data['MA20'] = data['Close'].rolling(window=20).mean()
            data['MA60'] = data['Close'].rolling(window=60).mean()

            # 2. MACD
            exp1 = data['Close'].ewm(span=12, adjust=False).mean()
            exp2 = data['Close'].ewm(span=26, adjust=False).mean()
            data['MACD'] = exp1 - exp2
            data['Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()
            data['Hist'] = data['MACD'] - data['Signal']

            # 3. KD指標 (9, 3, 3)
            low_9 = data['Low'].rolling(window=9).min()
            high_9 = data['High'].rolling(window=9).max()
            data['RSV'] = 100 * ((data['Close'] - low_9) / (high_9 - low_9))
            data['K'] = data['RSV'].ewm(com=2, adjust=False).mean()
            data['D'] = data['K'].ewm(com=2, adjust=False).mean()

            # --- 繪圖設定 (三排：K棒、MACD、KD) ---
            fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                               vertical_spacing=0.05, 
                               row_heights=[0.5, 0.25, 0.25])

            # 【第一排：K棒 + 四條均線】
            fig.add_trace(go.Candlestick(
                x=data.index, 
                open=data['Open'], high=data['High'],
                low=data['Low'], close=data['Close'], 
                name="K線",
                increasing_line_color='red', increasing_fillcolor='red',
                decreasing_line_color='green', decreasing_fillcolor='green'
            ), row=1, col=1)

            fig.add_trace(go.Scatter(x=data.index, y=data['MA5'], line=dict(color='blue', width=1), name="5MA"), row=1, col=1)
            fig.add_trace(go.Scatter(x=data.index, y=data['MA10'], line=dict(color='orange', width=1), name="10MA"), row=1, col=1)
            fig.add_trace(go.Scatter(x=data.index, y=data['MA20'], line=dict(color='purple', width=1), name="20MA"), row=1, col=1)
            fig.add_trace(go.Scatter(x=data.index, y=data['MA60'], line=dict(color='grey', width=1), name="60MA"), row=1, col=1)

            # 【第二排：MACD 上紅下綠】
            colors = ['red' if val >= 0 else 'green' for val in data['Hist']]
            fig.add_trace(go.Bar(x=data.index, y=data['Hist'], name="MACD柱狀", marker_color=colors), row=2, col=1)
            fig.add_trace(go.Scatter(x=data.index, y=data['MACD'], line=dict(color='black', width=1), name="DIF"), row=2, col=1)
            fig.add_trace(go.Scatter(x=data.index, y=data['Signal'], line=dict(color='blue', width=1), name="MACD線"), row=2, col=1)

            # 【第三排：KD 指標】
            fig.add_trace(go.Scatter(x=data.index, y=data['K'], line=dict(color='black', width=1.5), name="K值"), row=3, col=1)
            fig.add_trace(go.Scatter(x=data.index, y=data['D'], line=dict(color='orange', width=1.5), name="D值"), row=3, col=1)
            # 加上 20/80 分界線
            fig.add_hline(y=80, line_dash="dash", line_color="red", row=3, col=1)
            fig.add_hline(y=20, line_dash="dash", line_color="green", row=3, col=1)

            # 版面設定
            fig.update_layout(
                title=f"{ticker} 技術指標全方位分析",
                height=900,
                xaxis_rangeslider_visible=False,
                template="plotly_white",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.info("📈 數據載入中，請再次點擊「執行全方位分析」或稍候。")
