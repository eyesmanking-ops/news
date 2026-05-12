# -*- coding: utf-8 -*-
import os, requests, feedparser
from datetime import datetime, timedelta

def send_to_telegram(text):
    # 同時嘗試讀取兩種名稱，確保萬無一失
    token = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TG_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID") or os.getenv("TG_CHAT_ID")
    
    if not token:
        print("❌ 錯誤：仍然抓不到變數，請確認 GitHub Secrets 名稱是否為 TELEGRAM_BOT_TOKEN")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    
    try:
        resp = requests.post(url, data=payload, timeout=20)
        print(f"Telegram 回應: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"連線異常: {e}")

def main():
    SOURCES = {
        "中央社-政治": "https://feeds.feedburner.com/rsscna/politics",
        "中央社-社會": "https://feeds.feedburner.com/rsscna/social",
        "中央社-兩岸": "https://feeds.feedburner.com/rsscna/mainland",
        "自由時報-全部": "https://news.ltn.com.tw/rss/all.xml"
    }
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    # 抓取 24 小時內新聞確保測試有感
    time_threshold = datetime.utcnow() - timedelta(hours=24)
    summary_text = f"<b>▋ 新聞巡邏測試 ({datetime.now().strftime('%H:%M')})</b>\n"
    has_news = False

    for name, url in SOURCES.items():
        try:
            resp = requests.get(url, headers=headers, timeout=30)
            feed = feedparser.parse(resp.content)
            items = []
            for entry in feed.entries:
                items.append(f"• <a href='{entry.link}'>{entry.title}</a>")
                if len(items) >= 2: break # 每個媒體取兩則做測試
            
            if items:
                summary_text += f"\n<b>【{name}】</b>\n" + "\n".join(items) + "\n"
                has_news = True
        except:
            continue

    if has_news:
        send_to_telegram(summary_text)
    else:
        print("未抓取到新聞")

if __name__ == "__main__":
    main()
