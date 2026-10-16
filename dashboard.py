import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime

# ==========================================
# 1. 頁面基礎設定 (Page Configuration)
# ==========================================
st.set_page_config(
    page_title="財經與資服標案動態觀測站",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. 高質感 CSS 樣式注入 (Custom CSS)
# ==========================================
st.markdown("""
<style>
    /* 全局背景 */
    .stApp {
        background-color: #F8FAFC;
    }
    
    /* 頂部主標題橫幅 */
    .header-banner {
        background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 100%);
        padding: 24px 32px;
        border-radius: 16px;
        color: #FFFFFF;
        margin-bottom: 24px;
        box-shadow: 0 10px 15px -3px rgba(15, 23, 42, 0.15);
    }
    .header-title {
        font-size: 1.8rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .header-subtitle {
        font-size: 0.9rem;
        color: #94A3B8;
        margin-top: 6px;
    }

    /* 指標自訂卡片 */
    .metric-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .metric-label {
        font-size: 0.85rem;
        color: #64748B;
        font-weight: 600;
    }
    .metric-value {
        font-size: 1.6rem;
        font-weight: 800;
        color: #0F172A;
        margin: 4px 0;
    }
    .change-up { color: #DC2626; font-weight: 700; font-size: 0.85rem; } /* 台股紅：漲 */
    .change-down { color: #16A34A; font-weight: 700; font-size: 0.85rem; } /* 台股綠：跌 */

    /* 新聞卡片 */
    .news-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-left: 4px solid #2563EB;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 12px;
    }
    .news-tag {
        background-color: #EFF6FF;
        color: #1D4ED8;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 4px;
    }
    .news-title {
        font-size: 1rem;
        font-weight: 700;
        color: #1E293B;
        margin-top: 6px;
    }

    /* 側邊欄黑色質感 */
    [data-testid="stSidebar"] {
        background-color: #0F172A;
    }
    [data-testid="stSidebar"] * {
        color: #F1F5F9 !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. 側邊欄控制台 (Sidebar)
# ==========================================
st.sidebar.title("🎛️ 觀測站控制台")
st.sidebar.caption(f"📅 資料更新時間：{datetime.now().strftime('%Y-%m-%d %H:%M')}")

selected_stock = st.sidebar.selectbox(
    "📌 選擇資服關注標的",
    options=[
        "6214.TW (精誠)", 
        "3029.TW (零壹)", 
        "2480.TW (敦陽科)", 
        "4953.TWO (緯軟)", 
        "6689.TW (伊雲谷)", 
        "6183.TW (邁達特)"
    ]
)

budget_range = st.sidebar.slider(
    "🏛️ 標案預算篩選 (萬元)",
    min_value=50, max_value=5000, value=(100, 3000), step=50
)

st.sidebar.markdown("---")
st.sidebar.success("🟢 排程狀態：每日 09:00 AM 自動推播")

# ==========================================
# 4. 主頁橫幅與頂部指標 (Header & Metrics)
# ==========================================
st.markdown(f"""
<div class="header-banner">
    <div class="header-title">📊 每日國際財經、資服產業與政府標案儀表板</div>
    <div class="header-subtitle">即時監控台股資服族群行情、K線技術指標與政府採購網公部門標案動態</div>
</div>
""", unsafe_allow_html=True)

# 頂部四欄關鍵指標
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown("""
    <div class="metric-card">
        <div class="metric-label">加權指數 (TAIEX)</div>
        <div class="metric-value">23,450.2</div>
        <div class="change-up">▲ +185.3 (+0.80%)</div>
    </div>
    """, unsafe_allow_html=True)
with c2:
    st.markdown("""
    <div class="metric-card">
        <div class="metric-label">資服族群均價</div>
        <div class="metric-value">NT$ 112.5</div>
        <div class="change-up">▲ +1.85%</div>
    </div>
    """, unsafe_allow_html=True)
with c3:
    st.markdown("""
    <div class="metric-card">
        <div class="metric-label">今日公部門標案</div>
        <div class="metric-value">14 件</div>
        <div class="change-up">▲ 新增 3 件</div>
    </div>
    """, unsafe_allow_html=True)
with c4:
    st.markdown("""
    <div class="metric-card">
        <div class="metric-label">共契採購招標案</div>
        <div class="metric-value">5 件</div>
        <div class="metric-label" style="color:#2563EB; font-weight:700;">預算共 1.2 億</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 5. 分頁內容區塊 (Tabs)
# ==========================================
tab1, tab2, tab3 = st.tabs([
    "📈 資服族群股市與技術分析", 
    "🏛️ 公部門標案與共契動態", 
    "🌐 國際財經 & 資服焦點新聞"
])

# ------------------------------------------
# TAB 1: 股市與技術分析 (含 K線 + 成交量)
# ------------------------------------------
with tab1:
    ticker_code = selected_stock.split(" ")[0]
    stock_name = selected_stock.split(" ")[1]
    
    st.subheader(f"📊 {stock_name} ({ticker_code}) 技術面動態診斷")
    
    try:
        stock = yf.Ticker(ticker_code)
        df = stock.history(period="3mo")
        
        if not df.empty:
            df['MA5'] = df['Close'].rolling(window=5).mean()
            df['MA20'] = df['Close'].rolling(window=20).mean()
            
            # 建立副圖（上方 K 線圖 + 下方成交量圖）
            fig = make_subplots(
                rows=2, cols=1, 
                shared_xaxes=True, 
                vertical_spacing=0.08, 
                row_heights=[0.75, 0.25]
            )
            
            # K線圖
            fig.add_trace(go.Candlestick(
                x=df.index,
                open=df['Open'], high=df['High'],
                low=df['Low'], close=df['Close'],
                name="K線",
                increasing_line_color='#DC2626', # 紅漲
                decreasing_line_color='#16A34A'  # 綠跌
            ), row=1, col=1)
            
            # 均線
            fig.add_trace(go.Scatter(x=df.index, y=df['MA5'], line=dict(color='#F59E0B', width=1.5), name="5MA"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='#2563EB', width=1.5), name="20MA"), row=1, col=1)
            
            # 成交量
            colors = ['#DC2626' if c >= o else '#16A34A' for c, o in zip(df['Close'], df['Open'])]
            fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name="成交量"), row=2, col=1)
            
            fig.update_layout(
                xaxis_rangeslider_visible=False,
                height=500,
                margin=dict(l=20, r=20, t=20, b=20),
                template="plotly_white",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # AI 診斷卡片
            latest_close = df['Close'].iloc[-1]
            latest_ma5 = df['MA5'].iloc[-1]
            latest_ma20 = df['MA20'].iloc[-1]
            
            with st.container(border=True):
                st.markdown("##### 🤖 短期技術面即時評語")
                if latest_close > latest_ma5 and latest_ma5 > latest_ma20:
                    st.success(f"🟢 **強勢多頭排列**：最新收盤價 NT${latest_close:.1f} 站穩 5MA 與 20MA，短期趨勢持續向上。")
                elif latest_close < latest_ma5 and latest_ma5 < latest_ma20:
                    st.error(f"🔴 **弱勢空頭格局**：股價回落至均線下方，建議關注下方 20MA 支撐力道。")
                else:
                    st.warning(f"🟡 **高檔整理震盪**：股價於均線間震盪整理，等待成交量放大突破。")
    except Exception as e:
        st.error(f"股價數據讀取失敗：{e}")

# ------------------------------------------
# TAB 2: 公部門標案動態
# ------------------------------------------
with tab3 = tab2 # tab2 標案動態
with tab2:
    st.subheader("🏛️ 政府電子採購網招標與共同供應契約")
    
    # 模擬標案資料表
    tender_data = pd.DataFrame({
        "發布日期": ["2026-10-16", "2026-10-16", "2026-10-15", "2026-10-15", "2026-10-14"],
        "機關名稱": ["數位發展部", "國家衛生研究院", "經濟部產業技術司", "財政部財政資訊中心", "台北市政府資訊局"],
        "標案名稱": [
            "116年度政府網站共用版型建置與擴充案",
            "醫療巨量資料庫AI分析模組軟體開發",
            "產業創新研發整合系統維護與雲端擴整",
            "115-116年財政雲端資料庫系統共同供應契約案",
            "市民服務大平臺系統升級與資安防護調整"
        ],
        "預算金額 (萬元)": [1200, 850, 450, 2800, 350],
        "類別": ["網站建置", "軟體開發", "系統維護", "共同供應契約", "資安/軟體"],
        "截止投標日": ["2026-11-02", "2026-10-30", "2026-11-10", "2026-11-15", "2026-10-28"]
    })
    
    # 依側邊欄預算範圍篩選
    filtered_df = tender_data[
        (tender_data["預算金額 (萬元)"] >= budget_range[0]) & 
        (tender_data["預算金額 (萬元)"] <= budget_range[1])
    ]
    
    col_t1, col_t2 = st.columns([2, 1])
    
    with col_t1:
        st.markdown(f"**篩選結果（預算 {budget_range[0]} 萬 ~ {budget_range[1]} 萬元）**")
        st.dataframe(
            filtered_df,
            use_container_width=True,
            column_config={
                "預算金額 (萬元)": st.column_config.NumberColumn(format="%d 萬"),
                "截止投標日": st.column_config.DateColumn(format="YYYY-MM-DD")
            }
        )
        
    with col_t2:
        st.markdown("**📊 標案類別金額統計**")
        fig_pie = px.pie(
            filtered_df, 
            names="類別", 
            values="預算金額 (萬元)",
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig_pie.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=260)
        st.plotly_chart(fig_pie, use_container_width=True)

# ------------------------------------------
# TAB 3: 焦點新聞
# ------------------------------------------
with tab3:
    st.subheader("📰 每日國際財經與資服產業焦點要聞")
    
    n1, n2 = st.columns(2)
    with n1:
        st.markdown("""
        <div class="news-card">
            <span class="news-tag">國際財經</span>
            <div class="news-title">美聯儲降息預期升高，科技股強勢反彈</div>
            <p style="font-size:0.88rem; color:#475569; margin-top:6px;">
            通膨數據降溫，美股四大指數集體上揚，帶動全球科技股與資服板塊走強。
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="news-card">
            <span class="news-tag">雲端架構</span>
            <div class="news-title">全球 CSP 巨頭擴大資本支出，雲端搬遷需求強勁</div>
            <p style="font-size:0.88rem; color:#475569; margin-top:6px;">
            Microsoft 與 AWS 加碼資料中心建置，國內代理商與系統整合商訂單能見度高。
            </p>
        </div>
        """, unsafe_allow_html=True)

    with n2:
        st.markdown("""
        <div class="news-card">
            <span class="news-tag" style="background:#FEF3C7; color:#D97706;">國內資服</span>
            <div class="news-title">資服龍頭營收創同期新高，資安與 AI 為雙核心引擎</div>
            <p style="font-size:0.88rem; color:#475569; margin-top:6px;">
            企業數位轉型需求熱絡，金融與製造業資安升級帶動第三季營利成長。
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="news-card">
            <span class="news-tag" style="background:#FEF3C7; color:#D97706;">IPO / 興櫃</span>
            <div class="news-title">新創 AI 資服軟體商預計 Q4 登錄興櫃</div>
            <p style="font-size:0.88rem; color:#475569; margin-top:6px;">
            主打企業級 RAG 知識庫與 LLM 微調服務，已取得多家公部門與金融試行標案。
            </p>
        </div>
        """, unsafe_allow_html=True)
