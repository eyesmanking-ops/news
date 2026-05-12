# -*- coding: utf-8 -*-
import os, requests, feedparser

def send_to_telegram(text):
    token = os.getenv("TG_TOKEN")
    chat_id = os.getenv("TG_CHAT_ID")
    print(f"DEBUG: 準備發送訊息至 ID: {chat_id}")
    
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
    
    # 簡化來源，先測試這 4 家最穩定的
    SOURCES = {
        "中央社": "https://cna.com.tw",
        "自由時報": "https://ltn.com.tw",
        "中時新聞": "https://chinatimes.com",
        "聯合新聞": "https://udn.com"
    }
    
    summary_text = "<b>▋ 新聞巡邏測試</b>\n\n"
    has_news = False

    for name, url in SOURCES.items():
        print(f"DEBUG: 正在抓取 {name}...")
        try:
            # 加入 timeout 避免程式卡死
            resp = requests.get(url, timeout=10)
            feed = feedparser.parse(resp.content)
            
            items = []
            # 不看時間了，直接取最新 3 則，確保一定有東西發送
            for entry in feed.entries[:3]:
                items.append(f"• <a href='{entry.link}'>{entry.title}</a>")
            
            if items:
                summary_text += f"<b>{name}</b>\n" + "\n".join(items) + "\n\n"
                has_news = True
                print(f"DEBUG: {name} 抓取成功")
        except Exception as e:
            print(f"DEBUG: {name} 抓取失敗: {e}")

    if has_news:
        print("DEBUG: 準備呼叫發送函數")
        send_to_telegram(summary_text)
    else:
        print("DEBUG: 找不到任何新聞內容")

if __name__ == "__main__":
    main()
