# -*- coding: utf-8 -*-
import os, requests, feedparser
from datetime import datetime, timedelta

def send_to_telegram(text):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id: return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    # 3500字自動分段邏輯
    if len(text) > 3500:
        parts = text.split('\n<b>【') 
        current_msg = parts[0]
        for i in range(1, len(parts)):
            next_part = '\n<b>【' + parts[i]
            if len(current_msg) + len(next_part) > 3500:
                requests.post(url, data={"chat_id": chat_id, "text": current_msg, "parse_mode": "HTML", "disable_web_page_preview": True})
                current_msg = "<b>▋ 深度新聞巡邏 (續)</b>\n" + next_part
            else:
                current_msg += next_part
        requests.post(url, data={"chat_id": chat_id, "text": current_msg, "parse_mode": "HTML", "disable_web_page_preview": True})
    else:
        requests.post(url, data={"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True})

def main():
    # 依照你的需求配置的 4 間媒體、9 個頻道
    SOURCES = {
        "聯合-要聞": "https://udn.com/rssfeed/news/2/6638?ch=news",
        "聯合-社會": "https://udn.com/rssfeed/news/2/6644?ch=news",
        "聯合-地方": "https://udn.com/rssfeed/news/2/6645?ch=news",
        "聯合-經濟": "https://udn.com/rssfeed/news/2/6631?ch=news",
        "聯合-兩岸": "https://udn.com/rssfeed/news/2/6640?ch=news",
        "中時-即時總覽": "https://www.chinatimes.com/rss/realtimenews.xml",
        "青報-所有新聞": "https://www.ydn.com.tw/rss/news",
        "國教廣-教育新聞": "https://www.ner.gov.tw/news/?recordId=1",
        "國教廣-節目公告": "https://www.ner.gov.tw/news/?recordId=2"
    }
    
    history_file = "sent_links.txt"
    sent_links = set()
    if os.path.exists(history_file):
        with open(history_file, "r") as f:
            sent_links = set(f.read().splitlines())

    now_utc = datetime.utcnow()
    time_threshold = now_utc - timedelta(hours=12)
    headers = {'User-Agent': 'Mozilla/5.0'}
    summary_text = ""
    new_found_links = []

    for name, url in SOURCES.items():
        try:
            resp = requests.get(url, headers=headers, timeout=30)
            feed = feedparser.parse(resp.content)
            items = []
            for entry in feed.entries:
                link = entry.link
                if link not in sent_links:
                    try:
                        pub_time = datetime(*entry.published_parsed[:6])
                        if pub_time > time_threshold:
                            tw_time = (pub_time + timedelta(hours=8)).strftime('%H:%M')
                            items.append(f"• [{tw_time}] <a href='{link}'>{entry.title}</a>")
                            new_found_links.append(link)
                    except: continue
            if items:
                summary_text += f"\n<b>【{name} ({len(items)}則)】</b>\n" + "\n".join(items) + "\n"
        except: continue

    if summary_text:
        tw_now = (now_utc + timedelta(hours=8)).strftime('%m/%d %H:%M')
        final_msg = f"<b>▋ 深度新聞巡邏 ({tw_now})</b>\n" + summary_text
        send_to_telegram(final_msg)
        
        # 存回紀錄檔，與主任務共享紀錄以去重
        updated_history = list(sent_links) + new_found_links
        with open(history_file, "w") as f:
            f.write("\n".join(updated_history[-2000:])) # 稍微加大紀錄量

if __name__ == "__main__":
    main()
