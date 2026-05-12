# -*- coding: utf-8 -*-
import os, requests, feedparser
from datetime import datetime, timedelta

def send_to_telegram(text):
    # 1. 取得 Token 並進行「極限清理」
    raw_token = os.getenv("TG_TOKEN", "8654632376:AAFuCyZWI6CdSS6op76c1sELiJFP0hJ52h4")
    # 移除前後空白、換行符號，以及可能誤入的 "bot" 或 "/" 字眼
    token = raw_token.strip().replace(" ", "").replace("\n", "").replace("\r", "")
    if token.startswith("bot"):
        token = token[3:]
    if token.startswith("/"):
        token = token[1:]
        
    # 2. 取得 Chat ID 並清理
    chat_id = os.getenv("TG_CHAT_ID", "8741175747").strip()
    
    # 3. 正確拼接網址 (注意 bot 和 token 之間絕對不能有斜線)
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    
    print(f"DEBUG: 正在嘗試傳送至 Bot (Token開頭: {token[:5]}...)")
    
    try:
        resp = requests.post(url, data=payload, timeout=15)
        if resp.status_code != 200:
            print(f"DEBUG: 傳送失敗代碼 {resp.status_code}")
            print(f"DEBUG: 錯誤詳情 {resp.text}")
            print(f"DEBUG: 檢查網址格式是否為 .../bot數字:英文/... -> {url[:35]}...")
        else:
            print("Telegram 傳送成功！")
    except Exception as e:
        print(f"發送時發生異常: {e}")

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
