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
        "中央社": "https://feedburner.com",
        "自由時報": "https://ltn.com.tw",
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
            # 增加 verify=False 避免教育電台等網站的 SSL 憑證錯誤
            resp = requests.get(url, headers=headers, timeout=20, verify=False)
            resp.encoding = 'utf-8'
            feed = feedparser.parse(resp.text)
            
            items = []
            # 抓取過去 2 小時 (120分鐘)，確保內容充足
            time_limit = datetime.utcnow() - timedelta(minutes=120)
            
            for entry in feed.entries:
                pub_time = datetime.utcnow()
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_time = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                
                if pub_time > time_limit:
                    items.append(f"• <a href='{entry.link}'>{entry.title}</a>")
                if len(items) >= 5: break 
            
            if items:
                summary_text += f"<b>【{name}】</b>\n" + "\n".join(items) + "\n\n"
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
