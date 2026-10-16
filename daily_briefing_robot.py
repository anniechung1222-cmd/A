import os
import html
import requests
import feedparser
import yfinance as yf
from datetime import datetime

# 1. 抓取財經與資服新聞
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
                title = html.escape(entry.title)
                link = entry.link
                news_items.append(f"• [{category}] {title}\n  🔗 {link}")
        except Exception as e:
            news_items.append(f"• [{category}] 抓取失敗: {e}")
    if not news_items:
        return "• 暫無最新財經新聞"
    return "\n\n".join(news_items)

# 2. 評估全台資服族群行情
def fetch_stocks():
    stocks = {
        "6214.TW": "精誠", "3029.TW": "零壹", "2480.TW": "敦陽科", 
        "4953.TWO": "緯軟", "6689.TW": "伊雲谷", "6183.TW": "邁達特",
        "2453.TW": "凌群", "6741.TWO": "宏碁資訊", "6690.TWO": "安碁資訊", 
        "6902.TWO": "Gogolook", "6914.TWO": "意藍", "7701.TWO": "昕力資訊"
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
                code_number = ticker.split('.')[0]
                stock_results.append({
                    "name": html.escape(name), 
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
        f"📊 <b>全台資服族群概況 (含興櫃/上市櫃 {len(stock_results)} 檔)</b>\n"
        f"• 族群平均當日漲跌：<b>{avg_pct:+.2f}%</b>\n\n"
        f"🔥 <b>今日強勢領漲 Top 3</b>：\n{gainers_text}\n\n"
        f"❄️ <b>今日拉回弱勢 Top 3</b>：\n{losers_text}"
    )

# 3. 抓取資服 IPO / 興櫃專屬動態新聞
def fetch_ipo_news():
    try:
        url = "https://news.cnyes.com/rss/headline?cat=tw_stock_news"
        feed = feedparser.parse(url)
        ipo_keywords = ["IPO", "興櫃", "上市", "上櫃", "創櫃", "公開發行", "轉主板"]
        
        matched_news = []
        for entry in feed.entries:
            title = entry.title
            if any(kw in title for kw in ipo_keywords):
                escaped_title = html.escape(title)
                matched_news.append(f"• 🚀 {escaped_title}\n  🔗 {entry.link}")
                if len(matched_news) >= 2:
                    break
                    
        if matched_news:
            return "\n\n".join(matched_news)
        else:
            return "• 今日暫無最新資服 / 科技類 IPO 與興櫃變動公告"
    except Exception:
        return "• IPO 訊息抓取中"

# 4. 透過 g0v 開放 API 抓取政府電子採購網即時標案
def fetch_tenders():
    keywords = ["網站建置", "軟體開發", "共同供應契約"]
    results = []
    
    for kw in keywords:
        try:
            url = f"https://pcc.g0v.ronny.tw/api/v1/search?query={kw}"
            resp = requests.get(url, timeout=10)
            
            if resp.status_code == 200:
                data = resp.json()
                records = data.get("records", [])
                
                if records:
                    for item in records[:2]:
                        unit = html.escape(str(item.get("unit_name", "公部門機關")))
                        title = html.escape(str(item.get("brief", {}).get("title", "未具名標案")))
                        results.append(f"• [{kw}] {unit} - {title}")
                else:
                    results.append(f"• [{kw}] 近期尚無新增招標案")
            else:
                results.append(f"• [{kw}] API 回應異常 (HTTP {resp.status_code})")
        except Exception:
            results.append(f"• [{kw}] API 連線逾時")
            
    return "\n".join(results)

# 5. Telegram 自動發送
def send_telegram(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id, 
        "text": message, 
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    resp = requests.post(url, json=payload, timeout=15)
    print("Telegram API Status Code:", resp.status_code)
    print("Telegram API Response:", resp.text)
    if resp.status_code != 200:
        fallback_payload = {
            "chat_id": chat_id,
            "text": message.replace("<b>", "").replace("</b>", "").replace("<i>", "").replace("</i>", ""),
            "disable_web_page_preview": False
        }
        requests.post(url, json=fallback_payload, timeout=15)

def main():
    today = datetime.now().strftime("%Y-%m-%d")
    news = fetch_news()
    stocks = fetch_stocks()
    ipo_info = fetch_ipo_news()
    tenders = fetch_tenders()
    
    dashboard_url = "https://annie-finance-dashboard.streamlit.app/"
    
    report = (
        f"📊 <b>【每日情報晨報】{today}</b>\n\n"
        f"🌐 <b>一、國際財經與資服要事</b>：\n{news}\n\n"
        f"🚀 <b>二、資服業 IPO 與興櫃焦點</b>：\n{ipo_info}\n\n"
        f"📈 <b>三、資服族群行情速報</b>：\n{stocks}\n\n"
        f"🏛️ <b>四、公部門最新標案動態 (API介接)</b>：\n{tenders}\n\n"
        f"💡 <b>點擊開啟 Streamlit 彩色圖表儀表板：</b>\n"
        f'<a href="{dashboard_url}">{dashboard_url}</a>'
    )
    
    tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
    tg_chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if tg_token and tg_chat_id:
        send_telegram(tg_token, tg_chat_id, report)
        print("✅ Telegram 晨報已成功處理！")
    else:
        print("未偵測到 Telegram Secrets，報告預覽：\n", report)

if __name__ == "__main__":
    main()
