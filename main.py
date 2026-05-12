# -*- coding: utf-8 -*-
import os, requests, feedparser
from datetime import datetime, timedelta

def send_to_telegram(text):
    token = os.getenv("TG_TOKEN", "8654632376:AAFuCyZWI6CdSS6op76c1sELiJFP0hJ52h4")
    chat_id = os.getenv("TG_CHAT_ID", "8741175747")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    resp = requests.post(url, data=payload)
    print(f"Telegram 回應: {resp.text}")

def main():
    SOURCES = {
        "中央社-政治": "https://feeds.feedburner.com/rsscna/politics",
        "中央社-社會": "https://feeds.feedburner.com/rsscna/social",
        "中央社-兩岸": "https://feeds.feedburner.com/rsscna/mainland",
        "自由時報-全部": "https://news.ltn.com.tw/rss/all.xml"
    }
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    # 【測試建議】將分鐘改為 1440 (24小時)，先確保能抓到東西
    now_utc = datetime.utcnow()
    time_threshold = now_utc - timedelta(minutes=1440) 
    
    tw_now_str = (now_utc + timedelta(hours=8)).strftime('%m/%d %H:%M')
    summary_text = f"<b>▋ 測試巡邏 ({tw_now_str})</b>\n"
    has_news = False

    for name, url in SOURCES.items():
        try:
            resp = requests.get(url, headers=headers, timeout=30)
            feed = feedparser.parse(resp.content)
            print(f"DEBUG: {name} 總共發現 {len(feed.entries)} 則原始資料")
            
            items = []
            for entry in feed.entries:
                # 如果 published_parsed 抓不到，嘗試強制抓取所有新聞來測試
                items.append(f"• <a href='{entry.link}'>{entry.title}</a>")
                if len(items) >= 5: break # 每個媒體只取前 5 則，先測試通不通

            if items:
                summary_text += f"\n<b>【{name}】</b>\n" + "\n".join(items) + "\n"
                has_news = True
        except Exception as e:
            print(f"DEBUG: {name} 失敗: {e}")

    # 強制發送，不論有沒有新聞
    if has_news:
        send_to_telegram(summary_text)
    else:
        send_to_telegram("程式已執行，但未抓取到任何新聞內容。")

if __name__ == "__main__":
    main()
