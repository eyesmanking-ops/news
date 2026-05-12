# -*- coding: utf-8 -*-
import os, requests, feedparser

def send_to_telegram(text):
    token = os.getenv("TG_TOKEN")
    chat_id = os.getenv("TG_CHAT_ID")
    url = f"https://telegram.org{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    resp = requests.post(url, data=payload)
    print(f"DEBUG: Telegram 回應: {resp.text}")

def main():
    print("DEBUG: 程式開始執行")
    
    SOURCES = {
        "中央社": "https://cna.com.tw",
        "自由時報": "https://ltn.com.tw",
        "中時新聞": "https://chinatimes.com",
        "聯合新聞": "https://udn.com"
    }
    
    # 模擬 iPhone 瀏覽器身分，避免被報社阻擋
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
    }
    
    summary_text = "<b>▋ 新聞巡邏測試 (模擬瀏覽器版)</b>\n\n"
    has_news = False

    for name, url in SOURCES.items():
        print(f"DEBUG: 正在嘗試抓取 {name}...")
        try:
            # 1. 使用 headers 抓取內容
            resp = requests.get(url, headers=headers, timeout=15)
            # 2. 直接餵給 feedparser
            feed = feedparser.parse(resp.text)
            
            items = []
            # 測試階段：直接取前 3 則
            for entry in feed.entries[:3]:
                title = entry.title
                link = entry.link
                items.append(f"• <a href='{link}'>{title}</a>")
            
            if items:
                summary_text += f"<b>【{name}】</b>\n" + "\n".join(items) + "\n\n"
                has_news = True
                print(f"DEBUG: {name} 抓到 {len(items)} 則新聞")
            else:
                print(f"DEBUG: {name} 解析後內容為空 (可能 RSS 結構改變)")
                
        except Exception as e:
            print(f"DEBUG: {name} 發生錯誤: {e}")

    if has_news:
        print("DEBUG: 準備呼叫發送函數")
        send_to_telegram(summary_text)
    else:
        print("DEBUG: 全部媒體抓取失敗，請檢查 URL 或 Header")

if __name__ == "__main__":
    main()
