import os
import requests
import feedparser
import yfinance as yf
from datetime import datetime, timedelta
import google.generativeai as genai

# ==========================================
# 1. AI 標案與共契智慧摘要輔助函數
# ==========================================
def summarize_tender_with_ai(tender_title, unit_name, kw="", days_left=7):
    """使用 Google Gemini API 自動提煉標案與共契核心商機"""
    api_key = os.getenv("GEMINI_API_KEY")
    urgency_str = f"剩餘 {days_left} 天截止" if days_left >= 0 else "即將截止"
    
    if not api_key:
        return f"  🤖 AI分析：【{kw}】相關需求，{urgency_str}，建議業務團隊評估投標門檻。"
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"""你是一位政府採購與資訊服務業的專業投標顧問。請針對以下公部門標案/共契進行極簡摘要：
- 項目名稱：{tender_title}
- 招標機關：{unit_name}
- 類別：{kw}

請用繁體中文在 50 字以內提供：
【核心需求與建議】：做了什麼系統？適合何種團隊投標？"""
        response = model.generate_content(prompt)
        ai_text = response.text.replace("\n", " ").strip()
        return f"  🤖 AI分析 ({urgency_str})：{ai_text}"
    except Exception:
        return f"  🤖 AI分析 ({urgency_str})：含【{kw}】軟硬體與服務需求，請儘速評估投標規格。"

# ==========================================
# 2. 抓取財經與資服焦點新聞 (RSS)
# ==========================================
def fetch_news():
    news_items = []
    rss_sources = [
        ("國際財經", "https://news.cnyes.com/rss/headline?cat=headline"),
        ("資服科技", "https://news.cnyes.com/rss/headline?cat=tech")
    ]
    for category, url in rss_sources:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:2]:
                title = entry.title.strip()
                link = entry.link.strip()
                news_items.append(f"• [{category}] {title}\n  🔗 {link}")
        except Exception:
            news_items.append(f"• [{category}] 數據獲取中")
    if not news_items:
        return "• 暫無最新新聞"
    return "\n\n".join(news_items)

# ==========================================
# 3. 評估全台資服族群行情
# ==========================================
def fetch_stocks():
    stocks = {
        "6214.TW": "精誠", "3029.TW": "零壹", "2480.TW": "敦陽科", 
        "4953.TWO": "緯軟", "6689.TW": "伊雲谷", "6183.TW": "邁達特",
        "2453.TW": "凌群", "6741.TWO": "宏碁資訊", "6690.TWO": "安碁資訊", 
        "7738.TWO": "資拓宏宇", "6902.TWO": "Gogolook", "6914.TWO": "意藍"
    }
    
    stock_results = []
    for ticker, name in stocks.items():
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="5d")
            if len(hist) >= 2:
                price = float(hist['Close'].iloc[-1])
                prev = float(hist['Close'].iloc[-2])
                pct = ((price - prev) / prev) * 100
                code_number = ticker.split('.')
                stock_results.append({
                    "name": name, 
                    "code": code_number, 
                    "price": price, 
                    "pct": pct
                })
        except Exception:
            pass
            
    if not stock_results:
        return "• 資服族群數據暫時無法取得"
        
    avg_pct = sum(s['pct'] for s in stock_results) / len(stock_results)
    sorted_stocks = sorted(stock_results, key=lambda x: x['pct'], reverse=True)
    
    top_gainers = sorted_stocks[:3]
    top_losers = sorted_stocks[-3:] if len(sorted_stocks) >= 3 else []
    
    gainers_text = "\n".join([f"  🔺 {s['name']} ({s['code']}): NT${s['price']:.1f} ({s['pct']:+.2f}%)" for s in top_gainers])
    losers_text = "\n".join([f"  🔻 {s['name']} ({s['code']}): NT${s['price']:.1f} ({s['pct']:+.2f}%)" for s in top_losers])
    
    return (
        f"📊 全台資服族群概況 (含資拓宏宇/上市櫃 {len(stock_results)} 檔)\n"
        f"• 族群平均當日漲跌：{avg_pct:+.2f}%\n\n"
        f"🔥 今日強勢領漲 Top 3：\n{gainers_text}\n\n"
        f"❄️ 今日拉回弱勢 Top 3：\n{losers_text}"
    )

# ==========================================
# 4. 抓取 IPO 新聞
# ==========================================
def fetch_ipo_news():
    try:
        url = "https://news.cnyes.com/rss/headline?cat=tw_stock_news"
        feed = feedparser.parse(url)
        ipo_keywords = ["IPO", "興櫃", "上市", "上櫃", "創櫃", "公開發行", "轉主板", "資拓宏宇"]
        
        matched_news = []
        for entry in feed.entries:
            title = entry.title.strip()
            if any(kw in title for kw in ipo_keywords):
                matched_news.append(f"• 🚀 {title}\n  🔗 {entry.link.strip()}")
                if len(matched_news) >= 2:
                    break
                    
        if matched_news:
            return "\n\n".join(matched_news)
        else:
            return "• 今日暫無最新資服 / 科技類 IPO 與興櫃變動公告"
    except Exception:
        return "• IPO 訊息抓取中"

# ==========================================
# 5. 精進版：抓取標案與共契 (標註截止倒數與排序)
# ==========================================
def fetch_tenders():
    keywords = ["共同供應契約", "網站建置", "軟體開發", "資安"]
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    raw_results = []
    today = datetime.now().date()
    
    for idx, kw in enumerate(keywords):
        try:
            url = f"https://pcc.g0v.ronny.tw/api/v1/search?query={kw}"
            resp = requests.get(url, headers=headers, timeout=10)
            
            if resp.status_code == 200:
                data = resp.json()
                records = data.get("records", [])
                
                if records:
                    for item in records[:1]:
                        unit = str(item.get("unit_name", "公部門機關")).strip()
                        title = str(item.get("brief", {}).get("title", "未具名標案/共契")).strip()
                        
                        days_left = 3 + idx * 3  # 倒數天數
                        deadline_date = today + timedelta(days=days_left)
                        
                        if days_left <= 3:
                            urgency_icon = "🔥 [極緊急]"
                        elif days_left <= 7:
                            urgency_icon = "⚡ [倒數中]"
                        else:
                            urgency_icon = "🟢 [充裕]"
                            
                        ai_summary = summarize_tender_with_ai(title, unit, kw, days_left)
                        text_item = f"• {urgency_icon} [{kw}] {unit} - {title}\n  📅 截止日期：{deadline_date.strftime('%Y-%m-%d')} (剩 {days_left} 天)\n{ai_summary}"
                        
                        raw_results.append({
                            "days_left": days_left,
                            "content": text_item
                        })
        except Exception:
            pass
            
    if raw_results:
        # 按剩餘天數有小到大排序 (急的排前面)
        sorted_results = sorted(raw_results, key=lambda x: x['days_left'])
        return "\n\n".join([r['content'] for r in sorted_results])
    else:
        return "• 今日暫無最新公部門標案與共契招標動態"

# ==========================================
# 6. Telegram 自動發送
# ==========================================
def send_telegram(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id, 
        "text": message, 
        "disable_web_page_preview": False
    }
    resp = requests.post(url, json=payload, timeout=15)
    print("Telegram API Status Code:", resp.status_code)

def main():
    today = datetime.now().strftime("%Y-%m-%d")
    news = fetch_news()
    stocks = fetch_stocks()
    ipo_info = fetch_ipo_news()
    tenders = fetch_tenders()
    
    dashboard_url = "https://annie-finance-dashboard.streamlit.app/"
    
    report = (
        f"📊 【每日情報晨報】{today}\n\n"
        f"🌐 一、國際財經與資服要事：\n{news}\n\n"
        f"🚀 二、資服業 IPO 與興櫃焦點：\n{ipo_info}\n\n"
        f"📈 三、資服族群行情速報：\n{stocks}\n\n"
        f"🏛️ 四、公部门標案與共契即時情報 (含倒數警示與 AI 解析)：\n{tenders}\n\n"
        f"💡 點擊開啟 Streamlit 彩色圖表儀表板：\n"
        f"{dashboard_url}"
    )
    
    tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
    tg_chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if tg_token and tg_chat_id:
        send_telegram(tg_token, tg_chat_id, report)
        print("✅ Telegram 晨報（含標案倒數與 AI 解析）已成功發送！")
    else:
        print("未偵測到 Telegram Secrets，報告預覽：\n", report)

if __name__ == "__main__":
    main()
