# -*- coding: utf-8 -*-
import os, requests, feedparser, time
from datetime import datetime, timedelta

# 1. 媒體來源配置
SOURCES = {
    "中央社": "https://cna.com.tw",
    "自由時報": "https://ltn.com.tw",
    "教育電台": "https://ner.gov.tw",
    "中時新聞": "https://chinatimes.com",
    "聯合新聞": "https://udn.com",
    "青年日報": "https://ydn.com.tw"
}

def fetch_news():
    # 關鍵設定：只抓取過去 65 分鐘內的新聞 (多給 5 分鐘緩衝，確保不漏掉)
    # 使用 UTC 時間進行比較，因為 GitHub 伺服器預設是 UTC
    time_limit = datetime.utcnow() - timedelta(minutes=65)
    
    # 顯示給您看的標題改回台灣時間 (UTC+8)
    tw_now = datetime.utcnow() + timedelta(hours=8)
    summary_text = f"<b>▋ 新聞巡邏 ({tw_now.strftime('%m/%d %H:%M')})</b>\n\n"
    
    has_new_content = False
    emojis = {"中央社":"🔴","自由時報":"🟢","教育電台":"📻","中時新聞":"🔵","聯合新聞":"⚪","青年日報":"🎖️"}

    for name, url in SOURCES.items():
        try:
            feed = feedparser.parse(url)
            items = []
            
            for entry in feed.entries:
                # 判定新聞發布時間
                # feedparser 會將時間轉為 struct_time
                published_time = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published_time = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                
                # 如果抓不到時間，或者時間在 65 分鐘之前，就跳過
                if published_time and published_time < time_limit:
                    continue
                
                items.append(f"• <a href='{entry.link}'>{entry.title}</a>")
            
            if items:
                summary_text += f"{emojis.get(name, '▪️')} <b>{name}</b>\n" + "\n".join(items) + "\n\n"
                has_new_content = True
        except Exception as e:
            print(f"抓取 {name} 錯誤: {e}")
            
    return summary_text if has_new_content else None

def send_to_telegram(text):
    token = os.getenv("TG_TOKEN")
    chat_id = os.getenv("TG_CHAT_ID")
    if not token or not chat_id: return

    url = f"https://telegram.org{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    requests.post(url, data=payload)

if __name__ == "__main__":
    content = fetch_news()
    if content:
        send_to_telegram(content)
    else:
        print("過去一小時內沒有新新聞")
