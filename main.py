# -*- coding: utf-8 -*-
import os
import requests
import feedparser
from datetime import datetime, timedelta

def send_to_telegram(text):
    # 優先從 GitHub Secrets 讀取，若無則使用您提供的預設值
    token = os.getenv("TG_TOKEN", "8654632376:AAFuCyZWI6CdSS6op76c1sELiJFP0hJ52h4")
    chat_id = os.getenv("TG_CHAT_ID", "8741175747")
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    # 防止訊息過長導致發送失敗（Telegram 限制約 4096 字）
    if len(text) > 3500:
        parts = text.split('<b>【')
        current_msg = parts[0]
        for i in range(1, len(parts)):
            next_part = '<b>【' + parts[i]
            if len(current_msg) + len(next_part) > 3500:
                requests.post(url, data={"chat_id": chat_id, "text": current_msg, "parse_mode": "HTML", "disable_web_page_preview": True})
                current_msg = next_part
            else:
                current_msg += next_part
        requests.post(url, data={"chat_id": chat_id, "text": current_msg, "parse_mode": "HTML", "disable_web_page_preview": True})
    else:
        requests.post(url, data={"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True})

def main():
    # 您的核心監控媒體來源
    SOURCES = {
        "中央社-政治": "https://feeds.feedburner.com/rsscna/politics",
        "中央社-社會": "https://feeds.feedburner.com/rsscna/social",
        "中央社-兩岸": "https://feeds.feedburner.com/rsscna/mainland",
        "自由時報-全部": "https://news.ltn.com.tw/rss/all.xml"
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }

    # 設定抓取區間：抓取過去 90 分鐘內的新聞
    # (這能確保即使 GitHub Action 延遲啟動，也不會漏掉任何半小時一次的新聞)
    now_utc = datetime.utcnow()
    time_threshold = now_utc - timedelta(minutes=90)
    
    # 顯示用的台灣時間
    tw_now_str = (now_utc + timedelta(hours=8)).strftime('%m/%d %H:%M')
    summary_text = f"<b>▋ 核心巡邏：中央/自由 ({tw_now_str})</b>\n"
    has_news = False

    for name, url in SOURCES.items():
        try:
            resp = requests.get(url, headers=headers, timeout=30)
            feed = feedparser.parse(resp.content)
            
            items = []
            for entry in feed.entries:
                try:
                    # 解析新聞發布時間
                    pub_time = datetime(*entry.published_parsed[:6])
                    
                    if pub_time > time_threshold:
                        tw_time = (pub_time + timedelta(hours=8)).strftime('%H:%M')
                        items.append(f"• [{tw_time}] <a href='{entry.link}'>{entry.title}</a>")
                except:
                    continue
            
            if items:
                summary_text += f"\n<b>【{name} ({len(items)}則)】</b>\n" + "\n".join(items) + "\n"
                has_news = True
                
        except Exception as e:
            print(f"DEBUG: {name} 抓取失敗: {e}")

    if has_news:
        send_to_telegram(summary_text)
    else:
        # 若不想在沒新聞時收到訊息，可將下面這行註解掉
        print("此時段無新新聞")

if __name__ == "__main__":
    main()
