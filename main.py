import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 1. 頁面設定
st.set_page_config(page_title="專業多週期股票分析儀", layout="wide")

# --- 側邊欄配置 ---
with st.sidebar:
    st.header("🔍 搜尋與設定")
    quick_pick = st.selectbox("熱門標的", ["手動輸入", "2330.TW", "2454.TW", "0050.TW", "NVDA", "AAPL", "TSLA"])
    
    if quick_pick == "手動輸入":
        ticker_input = st.text_input("請輸入股票代號 (如 2330 或 6290)", "2330")
    else:
        ticker_input = quick_pick

    st.write("---")
    time_frame = st.radio("選擇分析週期", ["日線", "週線", "月線"], horizontal=True)
    analyze_btn = st.button("執行全方位分析", use_container_width=True)
    
    # 署名區：放在按鈕下方
    st.markdown("---")
    st.write("🛠️ **開發者：[雷兄]**")
    st.write("📈 不推薦任何投資！")
    st.write("📈 祝您投資順利！")
# 週期參數對應
interval_map = {"日線": "1d", "週線": "1wk", "月線": "1mo"}
period_map = {"日線": "1y", "週線": "5y", "月線": "max"}

if analyze_btn:
    with st.spinner(f'正在智慧偵測 {ticker_input} ...'):
        # --- 核心邏輯：自動切換上市/上櫃 ---
        raw_symbol = ticker_input.strip()
        stock_obj = None
        df = pd.DataFrame()
        final_ticker = raw_symbol

        if raw_symbol.isdigit():
            # 優先嘗試 .TW (上市)，若無則嘗試 .TWO (上櫃)
            for suffix in [".TW", ".TWO"]:
                test_ticker = raw_symbol + suffix
                temp_obj = yf.Ticker(test_ticker)
                temp_df = temp_obj.history(period="5d")
                if not temp_df.empty:
                    stock_obj = temp_obj
                    final_ticker = test_ticker
                    break
        else:
            stock_obj = yf.Ticker(raw_symbol)
            final_ticker = raw_symbol

        # 抓取分析數據
        if stock_obj:
            df = stock_obj.history(period=period_map[time_frame], interval=interval_map[time_frame])

        if df.empty:
            st.error(f"❌ 找不到資料 '{raw_symbol}'。")
        else:
            # 獲取名稱
            try:
                info = stock_obj.info
                c_name = info.get('shortName') or info.get('longName') or ""
                if "Taiwan Semiconductor" in c_name: c_name = "台積電"
            except:
                c_name = ""
                info = {}

            # 3. 計算技術指標
            df['MA20'] = df['Close'].rolling(window=20).mean()
            low_min, high_max = df['Low'].rolling(9).min(), df['High'].rolling(9).max()
            rsv = 100 * (df['Close'] - low_min) / (high_max - low_min)
            df['K'] = rsv.ewm(com=2, adjust=False).mean()
            df['D'] = df['K'].ewm(com=2, adjust=False).mean()
            exp1, exp2 = df['Close'].ewm(span=12).mean(), df['Close'].ewm(span=26).mean()
            df['MACD'] = exp1 - exp2
            df['Hist'] = df['MACD'] - df['MACD'].ewm(span=9).mean()

            # 4. 標題與面板
            st.title(f"📊 {final_ticker} {c_name} - {time_frame}")
            last, prev = df.iloc[-1], df.iloc[-2]
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("收盤價", f"{last['Close']:.2f}", f"{last['Close']-prev['Close']:.2f}")
            c2.metric("K 值", f"{last['K']:.1f}", f"{last['K']-prev['K']:.1f}")
            c3.metric("D 值", f"{last['D']:.1f}", f"{last['D']-prev['D']:.1f}")
            c4.metric("MACD 柱", f"{last['Hist']:.2f}", f"{last['Hist']-prev['Hist']:.2f}")

            # 5. K 線圖
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K棒'))
            fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='orange', width=1.5), name='20MA'))
            fig.update_layout(xaxis_rangeslider_visible=False, height=500, template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

            # 6. KD 與 MACD
            ck, cm = st.columns(2)
            with ck:
                st.write(f"### ⚡ KD (K: {last['K']:.1f})")
                kd_p = df[['K', 'D']].tail(100).copy()
                kd_p['80'], kd_p['20'] = 80, 20
                st.line_chart(kd_p, color=["#FF4B4B", "#0072B2", "#444444", "#444444"])
            with cm:
                st.write("### 🌊 MACD (上紅下黑)")
                m_colors = ['#FF4B4B' if v > 0 else '#111111' for v in df['Hist'].tail(100)]
                fig_m = go.Figure(go.Bar(x=df.index[-100:], y=df['Hist'].tail(100), marker_color=m_colors))
                fig_m.update_layout(height=300, template="plotly_dark", margin=dict(l=0, r=0, t=20, b=0))
                st.plotly_chart(fig_m, use_container_width=True)

            # 7. 價值區間預估
            st.write("---")
            st.write("### 💰 價值區間預估 (本益比估值法)")
            try:
                eps = info.get('trailingEps')
                if eps and eps > 0:
                    v1, v2, v3 = st.columns(3)
                    v1.metric("便宜價(12x)", f"{eps*12:.2f}")
                    v2.metric("合理價(15x)", f"{eps*15:.2f}")
                    v3.metric("偏高價(20x)", f"{eps*20:.2f}")
                    # 進度條
                    prog = max(0.0, min(1.0, (last['Close'] - eps*10) / (eps*12)))
                    st.progress(prog, text=f"目前股價位階：{'偏高' if prog > 0.7 else '便宜' if prog < 0.3 else '合理'}")
                elif eps and eps <= 0:
                    st.warning(f"⚠️ 公司目前虧損 (EPS: {eps})，不適用本益比估值。")
                else:
                    st.info("ℹ️ 暫無財報 EPS 數據，無法進行估值。")
            except:
                st.info("ℹ️ 估值區暫不可用。")