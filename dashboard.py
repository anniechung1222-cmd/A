import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
from datetime import datetime

# 頁面配置
st.set_page_config(
    page_title="財經與資服標案情報儀表板",
    page_icon="📊",
    layout="wide"
)

# 主標題
st.title("📈 每日國際財經、資服產業與政府標案動態觀測站")
st.caption(f"更新時間：{datetime.now().strftime('%Y-%m-%d %H:%M')}")

# 側邊欄
st.sidebar.title("🎛️ 儀表板控制台")
selected_stock = st.sidebar.selectbox(
    "📌 選擇資服關注標的",
    options=["6214.TW (精誠)", "3029.TW (零壹)", "2480.TW (敦陽科)", "4953.TWO (緯軟)", "6689.TW (伊雲谷)", "6183.TW (邁達特)"]
)

# 關鍵指標
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="加權指數 (TAIEX)", value="23,450.2", delta="+185.3 (+0.80%)")
with col2:
    st.metric(label="資服族群平均漲幅", value="NT$ 112.5", delta="+1.85%")
with col3:
    st.metric(label="今日新增公部門標案", value="14 件", delta="+3 件")

st.markdown("---")

# 頁籤分頁
tab1, tab2, tab3 = st.tabs(["🌐 國際財經 & 資服要事", "📈 資服族群股市診斷", "🏛️ 公部門標案情報"])

with tab1:
    st.subheader("📰 每日焦點要聞")
    st.info("🔹 **美聯儲降息預期升高，科技股強勢反彈**\n\n市場對於近期通膨數據降溫反應積極，美股四大指數集體上揚。")
    st.success("🔹 **資服龍頭營收創同期新高，資安與雲端轉型為雙核心引擎**\n\n企業數位轉型需求強勁，雲端搬遷與 AI 應用落地成為下半年營收主要動能。")

with tab2:
    ticker_code = selected_stock.split(" ")[0]
    stock_name = selected_stock.split(" ")[1]
    st.subheader(f"📊 {stock_name} ({ticker_code}) 技術分析")
    
    try:
        stock = yf.Ticker(ticker_code)
        df = stock.history(period="3mo")
        if not df.empty:
            df['MA5'] = df['Close'].rolling(window=5).mean()
            df['MA20'] = df['Close'].rolling(window=20).mean()
            
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="K線"))
            fig.add_trace(go.Scatter(x=df.index, y=df['MA5'], line=dict(color='orange', width=1.5), name="5MA"))
            fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='blue', width=1.5), name="20MA"))
            fig.update_layout(xaxis_rangeslider_visible=False, height=400)
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"數據載入失敗: {e}")

with tab3:
    st.subheader("🏛️ 最新政府電子採購網招標")
    tender_data = pd.DataFrame({
        "發布日期": ["2026-10-16", "2026-10-16", "2026-10-15"],
        "機關名稱": ["數位發展部", "國家衛生研究院", "經濟部產業技術司"],
        "標案名稱": [
            "116年度政府網站共用版型建置與擴充案",
            "醫療巨量資料庫AI分析模組軟體開發",
            "產業創新研發整合系統維護與雲端擴整"
        ],
        "預算金額 (萬元)": [1200, 450, 880],
        "類別": ["網站建置", "軟體開發", "系統維護"]
    })
    st.dataframe(tender_data, use_container_width=True)
