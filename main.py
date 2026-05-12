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
    
 # 2. 模擬 iPhone 11 的身份，這能騙過中時、聯合的阻擋機制
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
    }
    
    summary_text = f"<b>▋ 新聞巡邏 ({datetime.now().strftime('%m/%d %H:%M')})</b>\n\n"
    has_news = False

    # --- 這是第 48 行開始的內容 ---
    for name, url in SOURCES.items():
        print(f"DEBUG: 正在抓取 {name}...")
        try:
            resp = requests.get(url, headers=headers, timeout=20, verify=False)
            resp.encoding = 'utf-8'
            feed = feedparser.parse(resp.text)
            items = []
            for entry in feed.entries:
                title = getattr(entry, 'title', None)
                link = getattr(entry, 'link', None)
                if title and link:
                    items.append(f"• <a href='{link}'>{title}</a>")
            if items:
                summary_text += f"<b>【{name} 共 {len(items)} 則】</b>\n" + "\n".join(items) + "\n\n"
                has_news = True
                print(f"DEBUG: {name} 成功抓到 {len(items)} 則")
        except Exception as e:
            print(f"DEBUG: {name} 失敗: {str(e)[:30]}")

    if has_news:
        send_to_telegram(summary_text)
    else:
        send_to_telegram("📢 目前無新內容")


if __name__ == "__main__":
    # 忽略教育電台可能產生的 SSL 安全警告
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    main()
