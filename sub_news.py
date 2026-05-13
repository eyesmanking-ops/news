# -*- coding: utf-8 -*-
import os, requests, feedparser, io
from datetime import datetime, timedelta

def send_to_telegram(text):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id: return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
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
    # 改用 RSSHub 代理網址，繞過媒體對 GitHub IP 的封鎖
    SOURCES = {
        "聯合-要聞": "https://rsshub.app/udn/news/2/6638",
        "聯合-社會": "https://rsshub.app/udn/news/2/6644",
        "聯合-地方": "https://rsshub.app/udn/news/2/6645",
        "聯合-經濟": "https://rsshub.app/udn/news/2/6631",
        "聯合-兩岸": "https://rsshub.app/udn/news/2/6640",
        "中時-即時": "https://rsshub.app/chinatimes/realtimenews",
        "青報-所有": "https://rsshub.app/ydn",
        "國教廣-教育": "https://rsshub.app/ner/1"
    }
    
    history_file = "sent_links.txt"
    sent_links = set()
    if os.path.exists(history_file):
        with open(history_file, "r") as f:
            sent_links = set(f.read().splitlines())

    now_utc = datetime.utcnow()
    # 第一次跑建議放寬時間到 24 小時
    time_threshold = now_utc - timedelta(hours=24)
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    summary_text = ""
    new_found_links = []

    for name, url in SOURCES.items():
        print(f"正在透過中繼站檢查: {name}...")
        try:
            # 請求 RSSHub
            resp = requests.get(url, headers=headers, timeout=40)
            feed = feedparser.parse(io.BytesIO(resp.content))
            
            items = []
            if not feed.entries:
                print(f"⚠️ {name} 中繼站暫時無資料")
                continue

            for entry in feed.entries:
                link = entry.link
                if link not in sent_links:
                    dt_parsed = entry.get('published_parsed') or entry.get('updated_parsed')
                    if dt_parsed:
                        pub_time = datetime(*dt_parsed[:6])
                        if pub_time > time_threshold:
                            tw_time = (pub_time + timedelta(hours=8)).strftime('%H:%M')
                            items.append(f"• [{tw_time}] <a href='{link}'>{entry.title}</a>")
                            new_found_links.append(link)
                    else:
                        # 備案：若無時間則抓一則最新的
                        if not items:
                            items.append(f"• [新] <a href='{link}'>{entry.title}</a>")
                            new_found_links.append(link)
            
            if items:
                print(f"✅ {name} 成功抓到 {len(items)} 則")
                summary_text += f"\n<b>【{name} ({len(items)}則)】</b>\n" + "\n".join(items) + "\n"
        except Exception as e:
            print(f"❌ {name} 中繼站連線失敗: {str(e)}")

    if summary_text:
        tw_now = (now_utc + timedelta(hours=8)).strftime('%m/%d %H:%M')
        final_msg = f"<b>▋ 深度新聞巡邏 ({tw_now})</b>\n" + summary_text
        send_to_telegram(final_msg)
        
        with open(history_file, "a") as f:
            for l in new_found_links:
                f.write(l + "\n")
    else:
        print("最終結果：中繼站目前也抓不到新內容。")

if __name__ == "__main__":
    main()
