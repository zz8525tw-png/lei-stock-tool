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
        # 修正代號格式
        ticker = ticker_input.upper()
        if not ("." in ticker) and not ticker.isalpha():
            ticker += ".TW"
            
        # 抓取資料 (抓一年以確保 MA60 有足夠資料計算)
        data = yf.download(ticker, period="1y")
        
        if data.empty:
            st.error("找不到資料，請檢查代號。")
        else:
            # 計算均線 (MA)
            data['MA5'] = data['Close'].rolling(window=5).mean()
            data['MA10'] = data['Close'].rolling(window=10).mean()
            data['MA20'] = data['Close'].rolling(window=20).mean()
            data['MA60'] = data['Close'].rolling(window=60).mean()

            # 計算 MACD
            exp1 = data['Close'].ewm(span=12, adjust=False).mean()
            exp2 = data['Close'].ewm(span=26, adjust=False).mean()
            data['MACD'] = exp1 - exp2
            data['Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()
            data['Hist'] = data['MACD'] - data['Signal']

            # 建立子圖：第一排是K線圖(70%)，第二排是MACD(30%)
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                               vertical_spacing=0.05, row_heights=[0.7, 0.3])

            # 【1. K線圖核心】
            fig.add_trace(go.Candlestick(
                x=data.index, 
                open=data['Open'], high=data['High'],
                low=data['Low'], close=data['Close'], 
                name="K線"
            ), row=1, col=1)

            # 【2. 疊加四條均線】
            fig.add_trace(go.Scatter(x=data.index, y=data['MA5'], line=dict(color='blue', width=1), name="5MA"), row=1, col=1)
            fig.add_trace(go.Scatter(x=data.index, y=data['MA10'], line=dict(color='orange', width=1), name="10MA"), row=1, col=1)
            fig.add_trace(go.Scatter(x=data.index, y=data['MA20'], line=dict(color='purple', width=1), name="20MA(月)"), row=1, col=1)
            fig.add_trace(go.Scatter(x=data.index, y=data['MA60'], line=dict(color='green', width=1), name="60MA(季)"), row=1, col=1)

            # 【3. MACD 上紅下綠】
            colors = ['red' if val >= 0 else 'green' for val in data['Hist']]
            fig.add_trace(go.Bar(x=data.index, y=data['Hist'], name="MACD柱狀圖", marker_color=colors), row=2, col=1)
            fig.add_trace(go.Scatter(x=data.index, y=data['MACD'], line=dict(color='black', width=1), name="DIF"), row=2, col=1)
            fig.add_trace(go.Scatter(x=data.index, y=data['Signal'], line=dict(color='orange', width=1), name="MACD線"), row=2, col=1)

            # 版面設定
            fig.update_layout(
                title=f"{ticker} 趨勢技術分析",
                height=800,
                xaxis_rangeslider_visible=False,
                template="plotly_white",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.info("📈 數據更新中，請再次點擊「執行全方位分析」或稍候。")
