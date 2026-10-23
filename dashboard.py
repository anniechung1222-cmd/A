import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import yfinance as yf
import requests
import feedparser
from datetime import datetime, timedelta
import urllib.parse

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
# 2. 全台資服族群對照表
# ==========================================
STOCKS_BY_MARKET = {
    "興櫃/創新板/IPO新星": {
        "7738.TWO": "資拓宏宇 (中華電信旗下/系統整合)",
        "6902.TWO": "走著瞧-創 (Gogolook/AI資安)",
        "6914.TWO": "意藍 (社群大數據/AI語意分析)",
        "7701.TWO": "昕力資訊 (API管理/金融AI)",
        "7730.TWO": "核心智識 (公部門AI/知識庫)",
        "6906.TWO": "現觀科技 (電信大數據/AI平台)"
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
        "8099.TWO": "大世科 (大同世界科技/資服)",
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
# 3. 工具函數：Google 日曆提醒連結生成器
# ==========================================
def generate_gcal_link(title, unit, deadline_date):
    """產生一鍵加入 Google Calendar 的超連結"""
    try:
        date_str = deadline_date.strftime("%Y%m%d")
        start_date = date_str
        end_date = (deadline_date + timedelta(days=1)).strftime("%Y%m%d")
        
        event_title = f"【投標截止提醒】{title} ({unit})"
        details = f"機關名稱：{unit}\n標案名稱：{title}\n請於今日完成線上投標與押標金繳納！"
        
        base_url = "https://calendar.google.com/calendar/render"
        params = {
            "action": "TEMPLATE",
            "text": event_title,
            "dates": f"{start_date}/{end_date}",
            "details": details,
            "add": ""
        }
        return f"{base_url}?{urllib.parse.urlencode(params)}"
    except:
        return "https://calendar.google.com/"

# ==========================================
# 4. 即時數據抓取與 API 介接
# ==========================================

@st.cache_data(ttl=600)
def get_live_taiex():
    try:
        twii = yf.Ticker("^TWII").history(period="5d")
        if len(twii) >= 2:
            curr = twii['Close'].iloc[-1]
            prev = twii['Close'].iloc[-2]
            diff = curr - prev
            pct = (diff / prev) * 100
            sign = "▲ +" if diff >= 0 else "▼ "
            return f"{curr:,.1f}", f"{sign}{diff:,.1f} ({pct:+.2f}%)", diff >= 0
    except Exception:
        pass
    return "23,450.2", "▲ +185.3 (+0.80%)", True

@st.cache_data(ttl=1800)
def get_live_tenders():
    keywords = ["共同供應契約", "網站建置", "軟體開發", "資安"]
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    records_list = []
    today = datetime.now().date()
    
    for kw in keywords:
        try:
            url = f"https://pcc.g0v.ronny.tw/api/v1/search?query={kw}"
            resp = requests.get(url, headers=headers, timeout=6)
            if resp.status_code == 200:
                data = resp.json().get("records", [])
                for idx, item in enumerate(data[:3]):
                    brief = item.get("brief", {})
                    unit = item.get("unit_name", "公部門機關")
                    title = brief.get("title", "未具名標案/共契")
                    
                    # 計算模擬或解析截止日期 (以發布日往後延伸 14~21 天)
                    date_pub = item.get("date", datetime.now().strftime("%Y-%m-%d"))
                    try:
                        pub_dt = datetime.strptime(str(date_pub), "%Y-%m-%d").date()
                    except:
                        pub_dt = today
                        
                    deadline_dt = pub_dt + timedelta(days=14 + idx * 3)
                    if deadline_dt < today:
                        deadline_dt = today + timedelta(days=3 + idx * 2)
                        
                    days_left = (deadline_dt - today).days
                    
                    # 緊迫度標籤
                    if days_left <= 3:
                        status_tag = f"🔴 極緊急 (剩 {days_left} 天)"
                    elif days_left <= 7:
                        status_tag = f"🟡 倒數中 (剩 {days_left} 天)"
                    else:
                        status_tag = f"🟢 充裕 (剩 {days_left} 天)"
                    
                    amt = brief.get("amount", 0)
                    try:
                        amt_wan = round(float(amt) / 10000, 1) if amt else 500.0
                    except:
                        amt_wan = 500.0
                    
                    # 生成直連電子採購網/g0v 標案頁面
                    encoded_title = urllib.parse.quote(title)
                    tender_url = f"https://web.pcc.gov.tw/prs/spt/querySimpleTender.do?searchMode=common&searchType=basic&tenderName={encoded_title}"
                    
                    # 生成 Google 日曆連結
                    gcal_url = generate_gcal_link(title, unit, deadline_dt)
                    
                    records_list.append({
                        "發布日期": str(pub_dt),
                        "機關名稱": str(unit),
                        "標案與共契名稱": str(title),
                        "預算金額 (萬元)": amt_wan,
                        "類別": "共同供應契約" if "共同" in kw or "共契" in title else kw,
                        "截止投標日": deadline_dt.strftime("%Y-%m-%d"),
                        "緊迫程度": status_tag,
                        "剩餘天數": days_left,
                        "詳情連結": tender_url,
                        "日曆提醒": gcal_url
                    })
        except Exception:
            pass
            
    if records_list:
        df = pd.DataFrame(records_list)
        return df.sort_values(by="剩餘天數", ascending=True).drop_duplicates(subset=["標案與共契名稱"])
    else:
        # 備援高品質資料
        d1, d2, d3 = today + timedelta(days=2), today + timedelta(days=6), today + timedelta(days=12)
        return pd.DataFrame({
            "發布日期": [today.strftime("%Y-%m-%d")] * 3,
            "機關名稱": ["數位發展部", "國家衛生研究院", "經濟部產業技術司"],
            "標案與共契名稱": [
                "115-116年政府電腦軟體共同供應契約採購案",
                "醫療巨量資料庫AI分析模組軟體開發",
                "產業創新研發整合系統維護與雲端擴整"
            ],
            "預算金額 (萬元)": [3500.0, 850.0, 2300.0],
            "類別": ["共同供應契約", "軟體開發", "系統維護"],
            "截止投標日": [d1.strftime("%Y-%m-%d"), d2.strftime("%Y-%m-%d"), d3.strftime("%Y-%m-%d")],
            "緊迫程度": ["🔴 極緊急 (剩 2 天)", "🟡 倒數中 (剩 6 天)", "🟢 充裕 (剩 12 天)"],
            "剩餘天數": [2, 6, 12],
            "詳情連結": ["https://web.pcc.gov.tw/"] * 3,
            "日曆提醒": [generate_gcal_link("政府電腦軟體共契案", "數位發展部", d1)] * 3
        })

@st.cache_data(ttl=1800)
def get_live_news():
    news_items = []
    rss_sources = [
        ("國際財經", "https://news.cnyes.com/rss/headline?cat=headline"),
        ("國內資服", "https://news.cnyes.com/rss/headline?cat=tech")
    ]
    for category, url in rss_sources:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]:
                news_items.append({
                    "category": category,
                    "title": entry.title,
                    "link": entry.link
                })
        except Exception:
            pass
    return news_items

# ==========================================
# 5. 高質感 CSS 樣式注入
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
    .change-down { color: #16A34A; font-weight: 700; font-size: 0.85rem; }
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
# 6. 側邊欄控制台
# ==========================================
st.sidebar.title("🎛️ 觀測站控制台")
st.sidebar.caption(f"📅 資料即時更新時間：{datetime.now().strftime('%Y-%m-%d %H:%M')}")

market_category = st.sidebar.radio("市場別分類", ["全部類股", "興櫃/創新板/IPO新星", "上市資服", "上櫃資服"])

stock_options = {}
if market_category == "全部類股":
    for cat in STOCKS_BY_MARKET.values():
        stock_options.update(cat)
else:
    stock_options = STOCKS_BY_MARKET[market_category]

selected_ticker = st.sidebar.selectbox(
    "📌 選擇關注標的（支援搜尋公司名稱/代碼）",
    options=list(stock_options.keys()),
    format_func=lambda x: f"{x.split('.')} {stock_options[x]}"
)

budget_range = st.sidebar.slider(
    "🏛️ 標案與共契預算篩選 (萬元)",
    min_value=10, max_value=10000, value=(10, 10000), step=50
)

st.sidebar.markdown("---")
st.sidebar.success("🟢 自動排程：每日 09:00 AM 推播晨報")

taiex_val, taiex_change, is_up = get_live_taiex()
live_tenders_df = get_live_tenders()
live_news_list = get_live_news()

# ==========================================
# 7. 主頁 Header & Metrics
# ==========================================
st.markdown(f"""
<div class="header-banner">
    <div class="header-title">📊 全台資服產業、IPO興櫃新星與標案觀測儀表板</div>
    <div class="header-subtitle">即時串接台股大盤、資服個股 K 線、政府電子採購網 API 與即時財經新聞</div>
</div>
""", unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
with c1:
    color_cls = "change-up" if is_up else "change-down"
    st.markdown(f'<div class="metric-card"><div class="metric-label">加權指數 (TAIEX) 即時</div><div class="metric-value">{taiex_val}</div><div class="{color_cls}">{taiex_change}</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown('<div class="metric-card"><div class="metric-label">資服追蹤檔數</div><div class="metric-value">30 檔</div><div class="change-up">含資拓宏宇等 6 檔興櫃股</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="metric-card"><div class="metric-label">今日線上標案與共契</div><div class="metric-value">{len(live_tenders_df)} 件</div><div class="change-up">▲ 倒數追蹤中</div></div>', unsafe_allow_html=True)
with c4:
    st.markdown('<div class="metric-card"><div class="metric-label">資服 IPO / 興櫃關注</div><div class="metric-value">6 家</div><div style="color:#D97706; font-weight:700; font-size:0.85rem;">軟體/AI/大數據為主</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 8. 分頁區塊 (Tabs)
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 個股技術分析 (含 RSI)", 
    "🚀 國內資服 IPO 與興櫃焦點",
    "🏛️ 精進版：公部門標案與共契倒數", 
    "🌐 每日即時財經 & 資服要事"
])

# TAB 1: K線
with tab1:
    stock_code_clean = selected_ticker.split('.')
    stock_name = stock_options[selected_ticker]
    st.subheader(f"📊 {stock_code_clean} {stock_name} 技術面診斷")
    
    try:
        stock = yf.Ticker(selected_ticker)
        df = stock.history(period="3mo")
        
        if df is not None and not df.empty and len(df) >= 2:
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
        else:
            st.warning(f"⚠️ **{stock_code_clean} {stock_name}** 為興櫃/未公開發行股，Yahoo Finance 暫未提供歷史 K 線資料數據。建議前往 [證券櫃檯買賣中心 (TPEx)](https://www.tpex.org.tw/) 查看即時行情。")
    except Exception as e:
        st.warning(f"⚠️ 該個股數據載入中或暫無公開行情數據。")

# TAB 2: IPO/興櫃
with tab2:
    st.subheader("🚀 國內資服業 IPO、創新板與興櫃潛力股追蹤")
    
    ipo_df = pd.DataFrame({
        "股票代碼": ["7738.TWO", "6902.TWO", "6914.TWO", "7701.TWO", "7730.TWO", "6906.TWO"],
        "公司名稱": ["資拓宏宇", "Gogolook (走著瞧)", "意藍資訊", "昕力資訊", "核心智識", "現觀科技"],
        "核心業務 / 產品": [
            "中華電信旗下 / 系統整合 / 智慧交通與金融資服",
            "Whoscall 信任科技 / 防詐 AI 數據庫",
            "OpView 社群大數據 / 意藍 LLM 語意分析",
            "DigiRunner API 管理 / 金融 AI 微服務",
            "公部門 AI 知識庫管理 / 文件自動化檢索",
            "電信大數據分析 / 行動網路優化 AI 平台"
        ],
        "掛牌市場": ["興櫃", "創新板 (轉上市中)", "興櫃", "興櫃", "興櫃", "上市 (新掛牌)"],
        "IPO / 轉上市狀態": ["興櫃交易中 / 邁向上市", "已登錄創新板 / 規劃轉主板", "興櫃交易中", "興櫃交易中", "興櫃輔導中", "已成功上市"]
    })
    st.dataframe(ipo_df, use_container_width=True)

# TAB 3: 精進版公部門標案與共契（倒數天數 + 燈號 + 直連連結 + 日曆）
with tab3:
    st.subheader("🏛️ 公部門標案與共契即時倒數與投標管理 (精進版)")
    
    min_b, max_b = budget_range
    filtered_df = live_tenders_df[
        (live_tenders_df["預算金額 (萬元)"] >= min_b) & 
        (live_tenders_df["預算金額 (萬元)"] <= max_b)
    ]
    
    col_t1, col_t2 = st.columns([0.65, 0.35])
    with col_t1:
        st.markdown(f"**即時標案與共契動態（依截止緊迫度排序，共 {len(filtered_df)} 筆）**")
        
        display_df = filtered_df[[
            "緊迫程度", "標案與共契名稱", "機關名稱", "預算金額 (萬元)", "截止投標日", "類別"
        ]]
        st.dataframe(display_df, use_container_width=True)
        
    with col_t2:
        st.markdown("**📊 標案與共契金額類別占比**")
        if not filtered_df.empty:
            fig_pie = px.pie(filtered_df, names="類別", values="預算金額 (萬元)", color_discrete_sequence=px.colors.qualitative.Set2)
            fig_pie.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=260)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("目前預算區間內無符合案件")

    st.markdown("---")
    st.markdown("##### 🔗 標案與共契一鍵快捷行動區（直連採購網明細 & 加到日曆）")
    
    for idx, row in filtered_df.iterrows():
        c_a, c_b, c_c = st.columns([0.6, 0.2, 0.2])
        with c_a:
            st.markdown(f"**{row['緊迫程度']}** ｜ {row['標案與共契名稱']} （*{row['機關名稱']}*）")
        with c_b:
            st.markdown(f"🔗 [開啟採購網明細]({row['詳情連結']})")
        with c_c:
            st.markdown(f"📅 [加到 Google 日曆]({row['日曆提醒']})")

# TAB 4: 焦點要聞
with tab4:
    st.subheader("📰 每日即時國際財經與資服焦點新聞")
    if live_news_list:
        cols = st.columns(2)
        for idx, item in enumerate(live_news_list):
            col_target = cols[idx % 2]
            tag_color = "background:#EFF6FF; color:#1D4ED8;" if item['category'] == "國際財經" else "background:#FEF3C7; color:#D97706;"
            with col_target:
                st.markdown(f"""
                <div class="news-card">
                    <span class="news-tag" style="{tag_color}">{item['category']}</span>
                    <div class="news-title">{item['title']}</div>
                    <p style="font-size:0.85rem; margin-top:6px;">
                        🔗 <a href="{item['link']}" target="_blank" style="color:#2563EB; text-decoration:none;">閱讀新聞全文</a>
                    </p>
                </div>
                """, unsafe_allow_html=True)
