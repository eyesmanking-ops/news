# -*- coding: utf-8 -*-
import os, requests, feedparser
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
        resp = requests.post(url, data={"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True})
        print(f"Telegram 發送結果: {resp.status_code}")

def main():
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
    # 診斷期：將時間放寬到 24 小時，並確保不被紀錄檔擋掉
    time_threshold = now_utc - timedelta(hours=24) 
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    summary_text = ""
    new_found_links = []

    for name, url in SOURCES.items():
        print(f"正在檢查: {name}...")
        try:
            resp = requests.get(url, headers=headers, timeout=30)
            feed = feedparser.parse(resp.content)
            
            if not feed.entries:
                print(f"⚠️ {name} 抓取不到任何 entries，可能是格式不支援")
                continue
                
            items = []
            for entry in feed.entries:
                link = entry.link
                # 診斷期：先不管 sent_links，只要時間對就抓出來
                try:
                    # 嘗試多種可能的時間標籤
                    dt_parsed = entry.get('published_parsed') or entry.get('updated_parsed') or entry.get('created_parsed')
                    if dt_parsed:
                        pub_time = datetime(*dt_parsed[:6])
                        if pub_time > time_threshold:
                            tw_time = (pub_time + timedelta(hours=8)).strftime('%H:%M')
                            items.append(f"• [{tw_time}] <a href='{link}'>{entry.title}</a>")
                            new_found_links.append(link)
                    else:
                        # 如果沒時間戳記，就強行抓前三則來測試
                        if len(items) < 3:
                            items.append(f"• [新] <a href='{link}'>{entry.title}</a>")
                            new_found_links.append(link)
                except Exception as e:
                    print(f"解析 {name} 內容出錯: {e}")
                    continue
            
            if items:
                print(f"✅ {name} 成功抓到 {len(items)} 則新聞")
                summary_text += f"\n<b>【{name} ({len(items)}則)】</b>\n" + "\n".join(items) + "\n"
        except Exception as e:
            print(f"連線 {name} 失敗: {e}")

    if summary_text:
        tw_now = (now_utc + timedelta(hours=8)).strftime('%m/%d %H:%M')
        final_msg = f"<b>▋ 深度新聞巡邏 ({tw_now})</b>\n" + summary_text
        send_to_telegram(final_msg)
        
        with open(history_file, "a") as f: # 用 append 模式避免覆蓋
            f.write("\n".join(new_found_links) + "\n")
    else:
        print("❌ 最終結果：沒有符合條件的新聞可發送")

if __name__ == "__main__":
    main()
