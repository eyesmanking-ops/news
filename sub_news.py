# -*- coding: utf-8 -*-
import os, requests, feedparser, io, urllib.parse
from datetime import datetime, timedelta

GAS_PROXY_URL = "https://script.google.com/macros/s/AKfycbw5b5dbBYX9Quf0CeDAJmXHM5U9LbFZazS_fZ-U9PjXwi1fxGVULSg__2SjmAeo2J-l/exec"

def send_to_telegram(text):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id: return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True})

def main():
    SOURCES = {
        "聯合-要聞": "https://udn.com/rssfeed/news/2/6638?ch=news",
        "中時-即時": "https://www.chinatimes.com/rss/realtimenews.xml",
        "青報-所有": "https://www.ydn.com.tw/rss/news",
        "國教廣-教育": "https://www.ner.gov.tw/news/?recordId=1"
    }
    
    now_utc = datetime.utcnow()
    # 暴力測試：抓過去 7 天
    time_threshold = now_utc - timedelta(hours=168)
    summary_text = ""

    for name, target_url in SOURCES.items():
        print(f"🔍 檢查: {name}...")
        try:
            encoded_url = urllib.parse.quote(target_url, safe='')
            proxy_url = f"{GAS_PROXY_URL}?url={encoded_url}"
            resp = requests.get(proxy_url, timeout=45)
            
            # 除錯資訊
            print(f"   內容長度: {len(resp.text)} 字元")
            
            if "Error:" in resp.text:
                print(f"   ❌ 代理回傳錯誤: {resp.text}")
                continue

            feed = feedparser.parse(io.BytesIO(resp.content))
            items = []
            for entry in feed.entries[:5]: # 每個頻道先抓最新 5 則
                tw_time = "新"
                items.append(f"• [{tw_time}] <a href='{entry.link}'>{entry.title}</a>")
            
            if items:
                print(f"   ✅ 成功讀取 {len(items)} 則")
                summary_text += f"\n<b>【{name}】</b>\n" + "\n".join(items) + "\n"
        except Exception as e:
            print(f"   ❌ 出錯: {str(e)}")

    if summary_text:
        send_to_telegram(f"<b>▋ 深度新聞測試</b>\n" + summary_text)
        print("🚀 已發送至 Telegram")
    else:
        print("🛑 最終仍無內容。請檢查 GAS 部署是否正確設定為『所有人』。")

if __name__ == "__main__":
    main()
