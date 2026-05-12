# -*- coding: utf-8 -*-
import os, requests, feedparser, time
from datetime import datetime, timedelta

def send_to_telegram(text):
    token = os.getenv("TG_TOKEN")
    chat_id = os.getenv("TG_CHAT_ID")
    url = f"https://telegram.org{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    resp = requests.post(url, data=payload)
    print(f"DEBUG: Telegram 回應: {resp.text}")

def main():
    print("DEBUG: 程式開始執行")
    
    # 修正後的 2024/2025 最新 RSS 網址
    SOURCES = {
        "中央社": "https://feeds.feedburner.com/rsscna/politics",
        "自由時報": "https://news.ltn.com.tw/rss/all.xml",
        "中時新聞": "https://chinatimes.com",
        "聯合新聞": "https://udn.com",
        "青年日報": "https://ydn.com.tw",
        "教育電台": "https://ner.gov.tw"
    }
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    summary_text = f"<b>▋ 新聞巡邏 ({datetime.now().strftime('%H:%M')})</b>\n\n"
    has_news = False

    for name, url in SOURCES.items():
        print(f"DEBUG: 正在抓取 {name}...")
        try:
            # 增加 retry 機制，避免單次請求失敗
            resp = requests.get(url, headers=headers, timeout=20)
            # 強制使用 UTF-8 編碼
            resp.encoding = 'utf-8'
            feed = feedparser.parse(resp.text)
            
            items = []
            # 這次改為抓取「最近 1.5 小時」的新聞，確保銜接 GitHub Actions 的間隔
            time_limit = datetime.utcnow() - timedelta(minutes=95)
            
            for entry in feed.entries:
                # 嘗試抓取時間，若抓不到則預設為現在 (確保必有新聞)
                pub_time = datetime.utcnow()
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_time = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                
                if pub_time > time_limit:
                    items.append(f"• <a href='{entry.link}'>{entry.title}</a>")
                if len(items) >= 5: break # 每家最多 5 則
            
            if items:
                summary_text += f"<b>【{name}】</b>\n" + "\n".join(items) + "\n\n"
                has_news = True
                print(f"DEBUG: {name} 成功抓到 {len(items)} 則")
        except Exception as e:
            print(f"DEBUG: {name} 失敗: {str(e)[:50]}")

    if has_news:
        send_to_telegram(summary_text)
    else:
        # 如果還是空的，發送一個「系統存活」訊息，確保連線是通的
        send_to_telegram("📢 系統巡邏中：目前各報社暫無更新。")
        print("DEBUG: 無新新聞")

if __name__ == "__main__":
    main()
