import os
import requests
import feedparser
import yfinance as yf
from bs4 import BeautifulSoup
from datetime import datetime

# 1. 抓取新聞
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
                news_items.append(f"• [{category}] {entry.title}\n  🔗 {entry.link}")
        except Exception as e:
            news_items.append(f"• [{category}] 抓取失敗: {e}")
    return "\n\n".join(news_items)

# 2. 評估全台資服族群行情 (上市/上櫃/興櫃)
def fetch_stocks():
    stocks = {
        "6214.TW": "精誠", "3029.TW": "零壹", "2480.TW": "敦陽科", 
        "4953.TWO": "緯軟", "6689.TW": "伊雲谷", "6183.TW": "邁達特",
        "2453.TW": "凌群", "2471.TW": "資通", "6741.TWO": "宏碁資訊",
        "6690.TWO": "安碁資訊", "6752.TWO": "叡揚", "6914.TWO": "意藍",
        "6902.TWO": "走著瞧", "6865.TWO": "偉康科技"
    }
    
    stock_results = []
    for ticker, name in stocks.items():
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="5d")
            if len(hist) >= 2:
                price = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2]
                pct = ((price - prev) / prev) * 100
                stock_results.append({"name": name, "code": ticker.split('.')[0], "price": price, "pct": pct})
        except Exception:
            pass
            
    if not stock_results:
        return "• 資服族群數據暫時無法取得"
        
    avg_pct = sum(s['pct'] for s in stock_results) / len(stock_results)
    sorted_stocks = sorted(stock_results, key=lambda x: x['pct'], reverse=True)
    
    top_gainers = sorted_stocks[:3]
    top_losers = sorted_stocks[-3:]
    
    gainers_text = "\n".join([f"  🔺 {s['name']} ({s['code']}): NT${s['price']:.1f} ({s['pct']:+.2f}%)" for s in top_gainers])
    losers_text = "\n".join([f"  🔻 {s['name']} ({s['code']}): NT${s['price']:.1f} ({s['pct']:+.2f}%)" for s in top_losers])
    
    return (
        f"📊 **全台資服族群概況 (評估 {len(stock_results)} 檔)**\n"
        f"• 族群平均當日漲跌：**{avg_pct:+.2f}%**\n\n"
        f"🔥 **今日強勢領漲 Top 3**：\n{gainers_text}\n\n"
        f"❄️ **今日拉回弱勢 Top 3**：\n{losers_text}"
    )

# 3. 抓取政府標案
def fetch_tenders():
    keywords = ["網站建置", "軟體開發", "共同供應契約"]
    results = []
    headers = {"User-Agent": "Mozilla/5.0"}
    for kw in keywords:
        try:
            url = f"https://web.pcc.gov.tw/prkms/tender/common/basic/readTenderBasic?keyword={kw}"
            resp = requests.get(url, headers=headers, timeout=8)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                rows = soup.find_all('tr', class_='list_row')[:2]
                if rows:
                    for r in rows:
                        cols = r.find_all('td')
                        if len(cols) >= 3:
                            results.append(f"• [{kw}] {cols[1].text.strip()} - {cols[2].text.strip()}")
                else:
                    results.append(f"• [{kw}] 今日尚無新增招標")
        except Exception:
            results.append(f"• [{kw}] 查詢逾時")
    return "\n".join(results)

# 4. Telegram 推播
def send_telegram(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def main():
    today = datetime.now().strftime("%Y-%m-%d")
    news = fetch_news()
    stocks = fetch_stocks()
    tenders = fetch_tenders()
    
    report = (
        f"📊 **【每日情報晨報】{today}**\n\n"
        f"🌐 **一、國際財經與資服要事**：\n{news}\n\n"
        f"📈 **二、資服族群行情速報**：\n{stocks}\n\n"
        f"🏛️ **三、公部門最新標案動態**：\n{tenders}\n\n"
        f"💡 *進入您的 Streamlit 線上儀表板可查看全台資服股完整 K 線與 RSI 指標！*"
    )
    
    tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
    tg_chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if tg_token and tg_chat_id:
        send_telegram(tg_token, tg_chat_id, report)
        print("✅ Telegram 晨報已順利發送！")
    else:
        print("未偵測到 Telegram Secrets，報告內容預覽：\n", report)

if __name__ == "__main__":
    main()
