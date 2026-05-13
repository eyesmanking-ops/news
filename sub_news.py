# -*- coding: utf-8 -*-
import os, requests, feedparser, io
from datetime import datetime, timedelta

def send_to_telegram(text):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id: return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    # 保持分段邏輯
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
    # 修正部分網址
SOURCES = {
        # 聯合報使用 Feedburner 轉址版 (通常較難被封鎖)
        "聯合-要聞": "https://feeds.feedburner.com/udn/news",
        "聯合-社會": "https://feeds.feedburner.com/udn/social",
        "聯合-地方": "https://feeds.feedburner.com/udn/local",
        "聯合-經濟": "https://feeds.feedburner.com/udn/finance",
        "聯合-兩岸": "https://feeds.feedburner.com/udn/mainland",
        
        # 中時改用另一個路徑
        "中時-即時": "http://rss.chinatimes.com/rss/realtimenews-index.rss",
        
        # 青年日報與國教廣，我們嘗試加上更嚴格的 Cache-Control
        "青報-所有": "https://www.ydn.com.tw/rss/news",
        "國教廣-教育": "https://www.ner.gov.tw/news/?recordId=1",
    }
    
    history_file = "sent_links.txt"
    sent_links = set()
    if os.path.exists(history_file):
        with open(history_file, "r") as f:
            sent_links = set(f.read().splitlines())

    now_utc = datetime.utcnow()
    time_threshold = now_utc - timedelta(hours=12)
    # 模擬更真實的瀏覽器
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept': 'application/rss+xml, application/xml, text/xml, */*'
    }
    summary_text = ""
    new_found_links = []

    for name, url in SOURCES.items():
        print(f"正在檢查: {name}...")
        try:
            # 增加 verify=False 避免某些政府網站 SSL 過期問題
            resp = requests.get(url, headers=headers, timeout=30, verify=True)
            # 使用 io.BytesIO 確保 feedparser 能正確讀取 raw content
            feed = feedparser.parse(io.BytesIO(resp.content))
            
            items = []
            for entry in feed.entries:
                link = entry.link
                if link not in sent_links:
                    # 嘗試抓取時間
                    dt_parsed = entry.get('published_parsed') or entry.get('updated_parsed')
                    if dt_parsed:
                        pub_time = datetime(*dt_parsed[:6])
                        if pub_time > time_threshold:
                            tw_time = (pub_time + timedelta(hours=8)).strftime('%H:%M')
                            items.append(f"• [{tw_time}] <a href='{link}'>{entry.title}</a>")
                            new_found_links.append(link)
                    else:
                        # 如果抓不到時間，保險起見抓最新的前 2 則
                        if len(items) < 2:
                            items.append(f"• [新] <a href='{link}'>{entry.title}</a>")
                            new_found_links.append(link)
            
            if items:
                print(f"✅ {name} 成功抓到 {len(items)} 則")
                summary_text += f"\n<b>【{name} ({len(items)}則)】</b>\n" + "\n".join(items) + "\n"
        except Exception as e:
            print(f"❌ {name} 發生錯誤: {str(e)}")

    if summary_text:
        tw_now = (now_utc + timedelta(hours=8)).strftime('%m/%d %H:%M')
        final_msg = f"<b>▋ 深度新聞巡邏 ({tw_now})</b>\n" + summary_text
        send_to_telegram(final_msg)
        
        # 更新紀錄
        updated_history = list(sent_links) + new_found_links
        with open(history_file, "w") as f:
            f.write("\n".join(updated_history[-2000:]))
    else:
        print("最終結果：仍無新聞可發送。可能是來源網頁擋掉了 GitHub IP。")

if __name__ == "__main__":
    main()
