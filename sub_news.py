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
    SOURCES = {
        "聯合-要聞": "https://udn.com/rssfeed/news/2/6638?ch=news",
        "聯合-社會": "https://udn.com/rssfeed/news/2/6644?ch=news",
        "聯合-地方": "https://udn.com/rssfeed/news/2/6645?ch=news",
        "聯合-經濟": "https://udn.com/rssfeed/news/2/6631?ch=news",
        "聯合-兩岸": "https://udn.com/rssfeed/news/2/6640?ch=news",
        "中時-即時": "https://www.chinatimes.com/rss/realtimenews.xml",
        "青報-所有": "https://www.ydn.com.tw/rss/news",
        "國教廣-教育": "https://www.ner.gov.tw/news/?recordId=1"
    }
    
    history_file = "sent_links.txt"
    sent_links = set()
    if os.path.exists(history_file):
        with open(history_file, "r") as f:
            sent_links = set(f.read().splitlines())

    now_utc = datetime.utcnow()
    # 這裡將時間門檻設為 48 小時，確保測試時一定能抓到
    time_threshold = now_utc - timedelta(hours=48)
    
    # 關鍵：模仿最常見的 Chrome 瀏覽器，減少被擋機率
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
    }
    
    summary_text = ""
    new_found_links = []

    for name, url in SOURCES.items():
        print(f"正在嘗試抓取: {name}...")
        try:
            # 加上 stream=True 與更長的 timeout
            resp = requests.get(url, headers=headers, timeout=30, stream=True)
            if resp.status_code != 200:
                print(f"⚠️ {name} 回傳錯誤代碼: {resp.status_code}")
                continue
                
            feed = feedparser.parse(resp.content)
            items = []
            
            for entry in feed.entries:
                link = entry.link
                if link not in sent_links:
                    # 嘗試各種可能的時間欄位
                    dt_parsed = entry.get('published_parsed') or entry.get('updated_parsed')
                    if dt_parsed:
                        pub_time = datetime(*dt_parsed[:6])
                        if pub_time > time_threshold:
                            tw_time = (pub_time + timedelta(hours=8)).strftime('%H:%M')
                            items.append(f"• [{tw_time}] <a href='{link}'>{entry.title}</a>")
                            new_found_links.append(link)
                    else:
                        # 如果完全沒時間，抓最新的 1 則
                        if not items:
                            items.append(f"• [新] <a href='{link}'>{entry.title}</a>")
                            new_found_links.append(link)
            
            if items:
                print(f"✅ {name} 成功抓到 {len(items)} 則")
                summary_text += f"\n<b>【{name} ({len(items)}則)】</b>\n" + "\n".join(items) + "\n"
        except Exception as e:
            print(f"❌ {name} 抓取失敗: {str(e)}")

    if summary_text:
        tw_now = (now_utc + timedelta(hours=8)).strftime('%m/%d %H:%M')
        final_msg = f"<b>▋ 深度新聞巡邏 ({tw_now})</b>\n" + summary_text
        send_to_telegram(final_msg)
        with open(history_file, "a") as f:
            for l in new_found_links:
                f.write(l + "\n")
    else:
        print("最終結果：所有嘗試均失敗。這代表該主機 IP 已被徹底封鎖。")

if __name__ == "__main__":
    main()
