# -*- coding: utf-8 -*-
import os, requests, feedparser, time
from datetime import datetime, timedelta

def send_to_telegram(text):
    token = os.getenv("TG_TOKEN")
    chat_id = os.getenv("TG_CHAT_ID")
    
    # 注意：這裡必須改為 api.telegram.org 且要有 /bot
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    payload = {
        "chat_id": chat_id, 
        "text": text, 
        "parse_mode": "HTML", 
        "disable_web_page_preview": True
    }
    
    print(f"DEBUG: 嘗試發送至 Telegram API...")
    try:
        resp = requests.post(url, data=payload, timeout=15)
        print(f"DEBUG: Telegram 回應: {resp.text}")
    except Exception as e:
        print(f"DEBUG: 發送過程發生錯誤: {e}")


def main():
    print("DEBUG: 程式開始執行")
    
    SOURCES = {
        "中央社": "https://feeds.feedburner.com/rsscna/politics",
        "自由時報": "https://ltn.com.tw/rss/all.xml",
        "中時新聞": "https://chinatimes.com/rss/realtimenews-total.xml",
        "聯合新聞": "https://udn.com/rssfeed/news/2/6638?ch=news",
        "青年日報": "https://ydn.com.tw/rss/news/1",
        "教育電台": "https://ner.gov.tw/rss"
    }
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    summary_text = f"<b>▋ 新聞巡邏 ({datetime.now().strftime('%H:%M')})</b>\n\n"
    has_news = False

    for name, url in SOURCES.items():
        print(f"DEBUG: 正在抓取 {name}...")
        try:
            # 增加 verify=False 避免教育電台等網站的 SSL 憑證錯誤
            resp = requests.get(url, headers=headers, timeout=20, verify=False)
            resp.encoding = 'utf-8'
            feed = feedparser.parse(resp.text)
            
                       items = []
            # 1. 稍微放寬時間到 130 分鐘，確保銜接不遺漏
            time_limit = datetime.utcnow() - timedelta(minutes=130)
            
            for entry in feed.entries:
                # 2. 獲取新聞發布時間，若抓不到則預設為 None
                pub_time = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_time = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                
                # 3. 關鍵改動：如果解析不出時間(None)，或時間在 130 分鐘內，通通收錄
                # 同時刪除了原本 len(items) >= 5 的限制，保證抓到「全部」
                if pub_time is None or pub_time > time_limit:
                    items.append(f"• <a href='{entry.link}'>{entry.title}</a>")
            
            if items:
                # 這裡加入則數統計，方便您在手機上確認
                summary_text += f"<b>【{name} ({len(items)}則)】</b>\n" + "\n".join(items) + "\n\n"
                has_news = True
                print(f"DEBUG: {name} 成功抓到 {len(items)} 則")

        except Exception as e:
            print(f"DEBUG: {name} 失敗: {str(e)[:50]}")

    if has_news:
        send_to_telegram(summary_text)
    else:
        # 強制發送一個測試，確認通道已通
        send_to_telegram("📢 系統巡邏中：目前兩小時內暫無新內容。")

if __name__ == "__main__":
    # 忽略教育電台可能產生的 SSL 安全警告
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    main()
