import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime

# ==========================================
# 1. 頁面基礎設定 (Page Config)
# ==========================================
st.set_page_config(
    page_title="全台資服產業、IPO與標案觀測站",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. 全台資服族群對照表 (含 IPO/興櫃新星)
# ==========================================
STOCKS_BY_MARKET = {
    "興櫃/創新板/IPO新星": {
        "6902.TWO": "走著瞧-創 (Gogolook/AI資安)",
        "6914.TWO": "意藍 (社群大數據/AI文字分析)",
        "7701.TWO": "昕力資訊 (API管理/AI資服)",
        "7730.TWO": "核心智識 (公部門AI/知識庫)",
        "6906.TWO": "現觀科技 (電信大數據/AI)"
    },
    "上市資服": {
        "2427.TW": "三商電 (系統整合/金融端)",
        "2453.TW": "凌群 (系統整合/資安)",
        "2471.TW": "資通 (ERP/金融軟體)",
        "2480.TW": "敦陽科 (系統整合/資安)",
        "3029.TW": "零壹 (網路資安代理)",
        "6183.TW": "邁達特 (雲端/Cisco代理)",
        "6214.TW": "精誠 (資服龍頭/數據分析)",
        "6689.TW": "伊雲谷 (AWS雲端代理)"
    },
    "上櫃資服": {
        "3083.TWO": "網龍 (遊戲/軟體)",
        "3570.TWO": "大塚 (CAD/3D設計軟體)",
        "4953.TWO": "緯軟 (軟體外包開發)",
        "5201.TWO": "凱衛 (證券交易軟體)",
        "5202.TWO": "力新 (辦公軟體/OCR)",
        "5210.TWO": "寶碩 (金融資訊系統)",
        "5403.TWO": "中菲 (金融系統/資服)",
        "6148.TWO": "驊宏資 (資安/系統整合)",
        "6221.TWO": "晉泰 (網路基礎架構)",
        "6516.TWO": "勤崴國際 (高精地圖/車聯網)",
        "6690.TWO": "安碁資訊 (宏碁資安SOC)",
        "6741.TWO": "宏碁資訊 (微軟雲端代理)",
        "6752.TWO": "叡揚 (公文/雲端SaaS)",
        "6865.TWO": "偉康科技 (數位金融/身份認證)",
        "6874.TWO": "倍力 (軟體代理/碳盤查)"
    }
}

# ==========================================
# 3. 高質感 CSS 樣式注入
# ==========================================
st.markdown("""
<style>
    .stApp { background-color: #F8FAFC; }
    .header-banner {
        background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 100%);
        padding: 24px 32px;
        border-radius: 16px;
        color: #FFFFFF;
        margin-bottom: 24px;
        box-shadow: 0 10px 15px -3px rgba(15, 23, 42, 0.15);
    }
    .header-title { font-size: 1.8rem; font-weight: 800; margin: 0; }
    .header-subtitle { font-size: 0.9rem; color: #94A3B8; margin-top: 6px; }
    .metric-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .metric-label { font-size: 0.85rem; color: #64748B; font-weight: 600; }
    .metric-value { font-size: 1.6rem; font-weight: 800; color: #0F172A; margin: 4px 0; }
    .change-up { color: #DC2626; font-weight: 700; font-size: 0.85rem; }
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
    .ipo-tag {
        background-color: #FEF3C7;
        color: #D97706;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 4px;
    }
    .news-title { font-size: 1rem; font-weight: 700; color: #1E293B; margin-top: 6px; }
    [data-testid="stSidebar"] { background-color: #0F172A; }
    [data-testid="stSidebar"] * { color: #F1F5F9 !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. 側邊欄控制台
# ==========================================
st.sidebar.title("🎛️ 觀測站控制台")
st.sidebar.caption(f"📅 更新時間：{datetime.now().strftime('%Y-%m-%d %H:%M')}")

market_category = st.sidebar.radio("市場別分類", ["興櫃/創新板/IPO新星", "上市資服", "上櫃資服", "全部類股"])

if market_category == "全部類股":
    stock_options = {}
    for cat in STOCKS_BY_MARKET.values():
        stock_options.update(cat)
else:
    stock_options = STOCKS_BY_MARKET[market_category]

selected_ticker = st.sidebar.selectbox(
    "📌 選擇關注標的",
    options=list(stock_options.keys()),
    format_func=lambda x: f"{x.split('.')} {stock_options[x]}"
)

budget_range = st.sidebar.slider(
    "🏛️ 標案預算篩選 (萬元)",
    min_value=50, max_value=5000, value=(100, 3000), step=50
)

st.sidebar.markdown("---")
st.sidebar.success("🟢 自動排程：每日 09:00 AM 推播晨報")

# ==========================================
# 5. 主頁 Header & Metrics
# ==========================================
st.markdown(f"""
<div class="header-banner">
    <div class="header-title">📊 全台資服產業、IPO興櫃新星與標案儀表板</div>
    <div class="header-subtitle">包含興櫃登錄、創新板、上市櫃資服族群，即時監控 K 線、RSI 指標、IPO 動態與政府標案</div>
</div>
""", unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown('<div class="metric-card"><div class="metric-label">加權指數 (TAIEX)</div><div class="metric-value">23,450.2</div><div class="change-up">▲ +185.3 (+0.80%)</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown('<div class="metric-card"><div class="metric-label">資服追蹤檔數</div><div class="metric-value">28 檔</div><div class="change-up">含 5 檔 IPO/興櫃新星</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown('<div class="metric-card"><div class="metric-label">今日公部門標案</div><div class="metric-value">14 件</div><div class="change-up">▲ 新增 3 件</div></div>', unsafe_allow_html=True)
with c4:
    st.markdown('<div class="metric-card"><div class="metric-label">資服 IPO / 興櫃關注</div><div class="metric-value">5 家</div><div style="color:#D97706; font-weight:700; font-size:0.85rem;">軟體/AI/大數據為主</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 6. 分頁區塊 (Tabs)
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 個股技術分析 (含 RSI)", 
    "🚀 國內資服 IPO 與興櫃焦點",
    "🏛️ 公部門標案與共契情報", 
    "🌐 國際財經 & 資服焦點新聞"
])

# TAB 1: K線 + 成交量 + RSI 指標
with tab1:
    stock_name = stock_options[selected_ticker]
    st.subheader(f"📊 {selected_ticker.split('.')} {stock_name} 技術面診斷")
    
    try:
        stock = yf.Ticker(selected_ticker)
        df = stock.history(period="3mo")
        
        if not df.empty:
            df['MA5'] = df['Close'].rolling(window=5).mean()
            df['MA20'] = df['Close'].rolling(window=20).mean()
            
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            fig = make_subplots(
                rows=3, cols=1, 
                shared_xaxes=True, 
                vertical_spacing=0.05, 
                row_heights=[0.55, 0.20, 0.25]
            )
            
            fig.add_trace(go.Candlestick(
                x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                name="K線", increasing_line_color='#DC2626', decreasing_line_color='#16A34A'
            ), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['MA5'], line=dict(color='#F59E0B', width=1.5), name="5MA"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='#2563EB', width=1.5), name="20MA"), row=1, col=1)
            
            colors = ['#DC2626' if c >= o else '#16A34A' for c, o in zip(df['Close'], df['Open'])]
            fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name="成交量"), row=2, col=1)
            
            fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='#8B5CF6', width=1.5), name="14日 RSI"), row=3, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
            
            fig.update_layout(
                xaxis_rangeslider_visible=False, height=550,
                margin=dict(l=20, r=20, t=20, b=20), template="plotly_white",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            latest_close = df['Close'].iloc[-1]
            latest_ma5 = df['MA5'].iloc[-1]
            latest_ma20 = df['MA20'].iloc[-1]
            latest_rsi = df['RSI'].iloc[-1] if not pd.isna(df['RSI'].iloc[-1]) else 50
            
            with st.container(border=True):
                st.markdown("##### 🤖 短期技術面即時評語")
                col_diag1, col_diag2 = st.columns(2)
                with col_diag1:
                    if latest_close > latest_ma5 and latest_ma5 > latest_ma20:
                        st.success(f"🟢 **均線多頭排列**：最新收盤價 NT${latest_close:.1f} 站穩 5MA 與 20MA，動能強勁。")
                    elif latest_close < latest_ma5 and latest_ma5 < latest_ma20:
                        st.error(f"🔴 **均線空頭格局**：股價位於均線下方，宜關注 20MA 支撐力道。")
                    else:
                        st.warning(f"🟡 **高檔整理區間**：股價於均線間震盪，等待成交量帶頭突破。")
                with col_diag2:
                    if latest_rsi > 70:
                        st.error(f"🔴 **RSI ({latest_rsi:.1f}) > 70 (超買)**：短線漲幅較急，留意短線拉回風險。")
                    elif latest_rsi < 30:
                        st.success(f"🟢 **RSI ({latest_rsi:.1f}) < 30 (超賣)**：進入超賣區，可觀察止跌築底訊號。")
                    else:
                        st.info(f"⚪ **RSI ({latest_rsi:.1f}) 正常**：指標處於 30~70 健康整理區間。")
    except Exception as e:
        st.error(f"無法取得該股票數據：{e}")

# TAB 2: 資服 IPO 與興櫃新星專區
with tab2:
    st.subheader("🚀 國內資服業 IPO、創新板與興櫃潛力股追蹤")
    
    st.markdown("此專區監控具備 **AI 應用、大數據分析、雲端資安與數位轉型** 核心技術之興櫃與創新規劃公司：")
    
    ipo_df = pd.DataFrame({
        "股票代碼": ["6902.TWO", "6914.TWO", "7701.TWO", "7730.TWO", "6906.TWO"],
        "公司名稱": ["Gogolook (走著瞧)", "意藍資訊", "昕力資訊", "核心智識", "現觀科技"],
        "核心業務 / 產品": [
            "Whoscall 信任科技 / 防詐 AI 數據庫",
            "OpView 社群大數據 / 意藍 LLM 語意分析",
            "DigiRunner API 管理 / 金融 AI 微服務",
            "公部門 AI 知識庫管理 / 文件自動化檢索",
            "電信大數據分析 / 行動網路優化 AI 平台"
        ],
        "掛牌市場": ["創新板 (轉上市中)", "興櫃", "興櫃", "興櫃", "上市 (新掛牌)"],
        "IPO / 轉上市狀態": ["已登錄創新板 / 規劃轉主板", "興櫃交易中", "興櫃交易中", "興櫃輔導中", "已成功上市"]
    })
    
    st.dataframe(ipo_df, use_container_width=True)
    st.markdown("---")
    st.markdown("##### 📰 最新資服業 IPO 與公開發行動態")
    
    col_ipo1, col_ipo2 = st.columns(2)
    with col_ipo1:
        st.markdown("""
        <div class="news-card">
            <span class="ipo-tag">IPO 輔導</span>
            <div class="news-title">新創 AI 軟體業者啟動 IPO 輔導，擬申請創新板掛牌</div>
            <p style="font-size:0.88rem; color:#475569; margin-top:6px;">
            主打企業級 RAG 知識庫與生成式 AI 微調服務，受惠金融與公部門轉型需求，近兩年營收成長逾 40%。
            </p>
        </div>
        """, unsafe_allow_html=True)
    with col_ipo2:
        st.markdown("""
        <div class="news-card">
            <span class="ipo-tag">興櫃轉上市</span>
            <div class="news-title">資安與大數據服務商遞件申請興櫃轉主板上市</div>
            <p style="font-size:0.88rem; color:#475569; margin-top:6px;">
            證交所審議通過多檔科技創新股上市案，資服產業群聚效應在台灣資本市場逐漸形成。
            </p>
        </div>
        """, unsafe_allow_html=True)

# TAB 3: 公部門標案情報
with tab3:
    st.subheader("🏛️ 政府電子採購網招標與共同供應契約")
    
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
        "預算金額 (萬元)":,
        "類別": ["網站建置", "軟體開發", "系統維護", "共同供應契約", "資安/軟體"],
        "截止投標日": ["2026-11-02", "2026-10-30", "2026-11-10", "2026-11-15", "2026-10-28"]
    })
    
    filtered_df = tender_data[
        (tender_data["預算金額 (萬元)"] >= budget_range) & 
        (tender_data["預算金額 (萬元)"] <= budget_range)
    ]
    
    col_t1, col_t2 = st.columns([0.6, 0.4])
    with col_t1:
        st.markdown(f"**篩選結果（預算 {budget_range} 萬 ~ {budget_range} 萬元）**")
        st.dataframe(filtered_df, use_container_width=True)
    with col_t2:
        st.markdown("**📊 標案類別金額統計**")
        fig_pie = px.pie(filtered_df, names="類別", values="預算金額 (萬元)", color_discrete_sequence=px.colors.qualitative.Set2)
        fig_pie.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=260)
        st.plotly_chart(fig_pie, use_container_width=True)

# TAB 4: 焦點要聞
with tab4:
    st.subheader("📰 每日國際財經與資服焦點新聞")
    n1, n2 = st.columns(2)
    with n1:
        st.markdown("""
        <div class="news-card">
            <span class="news-tag">國際財經</span>
            <div class="news-title">美聯儲降息預期升高，科技股強勢反彈</div>
            <p style="font-size:0.88rem; color:#475569; margin-top:6px;">通膨數據降溫，美股四大指數集體上揚，帶動全球科技股與資服板塊走強。</p>
        </div>
        """, unsafe_allow_html=True)
    with n2:
        st.markdown("""
        <div class="news-card">
            <span class="news-tag" style="background:#FEF3C7; color:#D97706;">國內資服</span>
            <div class="news-title">資服龍頭營收創同期新高，資安與 AI 為雙核心引擎</div>
            <p style="font-size:0.88rem; color:#475569; margin-top:6px;">企業數位轉型需求熱絡，金融與製造業資安升級帶動第三季營利成長。</p>
        </div>
        """, unsafe_allow_html=True)
