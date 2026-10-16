import os
import requests
import feedparser
import yfinance as yf
from bs4 import BeautifulSoup
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
                news_items.append(f"• [{category}] {entry.title}\n  🔗 {entry.link}")
        except Exception as e:
            news_items.append(f"• [{category}] 抓取失敗: {e}")
    return "\n\n".join(news_items)

# 2. 抓取資服股技術面
def fetch_stocks():
    stocks = {"6214.TW": "精誠", "3029.TW": "零壹", "2480.TW": "敦陽科", "4953.TWO": "緯軟"}
    reports = []
    for ticker, name in stocks.items():
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1mo")
            if len(hist) >= 2:
                price = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2]
                pct = ((price - prev) / prev) * 100
                ma5 = hist['Close'].tail(5).mean()
                ma20 = hist['Close'].tail(20).mean()
                status = "📈 多頭" if price > ma5 and ma5 > ma20 else ("📉 空頭" if price < ma5 and ma5 < ma20 else "➖ 震盪")
                reports.append(f"• {name}: NT${price:.1f} ({pct:+.2f}%) | 趨勢: {status}")
        except Exception:
            pass
    return "\n".join(reports)

# 3. 抓取公部門標案
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
                            results.append(f"• [{kw}] {cols.text.strip()} - {cols.text.strip()}")
                else:
                    results.append(f"• [{kw}] 今日尚無新增招標")
        except Exception:
            results.append(f"• [{kw}] 查詢逾時")
    return "\n".join(results)

# 4. Telegram 推播
def send_telegram(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    requests.post(url, json=payload)

def main():
    today = datetime.now().strftime("%Y-%m-%d")
    news = fetch_news()
    stocks = fetch_stocks()
    tenders = fetch_tenders()
    
    report = (
        f"📊 【每日情報晨報】{today}\n\n"
        f"🌐 國際財經與資服要事：\n{news}\n\n"
        f"📈 資服族群行情：\n{stocks}\n\n"
        f"🏛️ 公部門標案動態：\n{tenders}\n\n"
        f"💡 請登入您的 Streamlit 儀表板查看完整動態圖表！"
    )
    
    tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
    tg_chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if tg_token and tg_chat_id:
        send_telegram(tg_token, tg_chat_id, report)
        print("✅ Telegram 訊息已發送")
    else:
        print("未設定 Telegram Token，晨報預覽：\n", report)

if __name__ == "__main__":
    main()
