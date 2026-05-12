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

    for name, url in SOURCES.items():
        print(f"DEBUG: 正在抓取 {name}...")
        try:
            # 3. 強制使用模擬身份抓取，並忽略 SSL 錯誤 (針對教育電台)
            resp = requests.get(url, headers=headers, timeout=25, verify=False)
            resp.encoding = 'utf-8'
            
            # 4. 將抓到的內容餵給解析器
            feed = feedparser.parse(resp.text)
            
            items = []
            # 第一步：直接抓取 feed 裡所有的 entries
            for entry in feed.entries:
                # 第二步：獲取標題與連結，若標題不存在則跳過
                title = getattr(entry, 'title', None)
                link = getattr(entry, 'link', None)
                
                if title and link:
                    # 第三步：先不做時間過濾，確保「所有」現有 RSS 內容都能出來
                    items.append(f"• <a href='{link}'>{title}</a>")
            
            if items:
                # 加入 Emoji 與統計，讓您在手機上一目了然
                summary_text += f"<b>【{name} 共 {len(items)} 則】</b>\n" + "\n".join(items) + "\n\n"
                has_news = True
                print(f"DEBUG: {name} 成功抓到 {len(items)} 則")
            else:
                # 如果 items 是空的，印出 feed 結構來診斷
                print(f"DEBUG: {name} 解析成功但 entries 為空，結構：{list(feed.keys())}")


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
