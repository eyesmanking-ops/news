# -*- coding: utf-8 -*-
import os, requests, feedparser, io, urllib.parse
from datetime import datetime, timedelta

# ==========================================
# 已嵌入您的 Google 代理網址
# ==========================================
GAS_PROXY_URL = "https://script.google.com/macros/s/AKfycbw5b5dbBYX9Quf0CeDAJmXHM5U9LbFZazS_fZ-U9PjXwi1fxGVULSg__2SjmAeo2J-l/exec"

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
    # 第一次執行建議抓 24 小時內，確保有新聞產出
    time_threshold = now_utc - timedelta(hours=24)
    summary_text = ""
    new_found_links = []

    for name, target_url in SOURCES.items():
        print(f"正在透過 Google 代理抓取: {name}...")
        try:
            # 對目標網址編碼，確保 Google Script 能正確接收
            encoded_url = urllib.parse.quote(target_url, safe='')
            proxy_url = f"{GAS_PROXY_URL}?url={encoded_url}"
            
            resp = requests.get(proxy_url, timeout=45)
            if resp.status_code != 200:
                print(f"⚠️ {name} 代理連線異常 (HTTP {resp.status_code})")
                continue
                
            feed = feedparser.parse(io.BytesIO(resp.content))
            items = []
            
            for entry in feed.entries:
                link = entry.link
                if link not in sent_links:
                    # 優先讀取時間，若無則強制抓取
                    dt_parsed = entry.get('published_parsed') or entry.get('updated_parsed')
                    if dt_parsed:
                        pub_time = datetime(*dt_parsed[:6])
                        if pub_time > time_threshold:
                            tw_time = (pub_time + timedelta(hours=8)).strftime('%H:%M')
                            items.append(f"• [{tw_time}] <a href='{link}'>{entry.title}</a>")
                            new_found_links.append(link)
                    else:
                        if len(items) < 2:
                            items.append(f"• [新] <a href='{link}'>{entry.title}</a>")
                            new_found_links.append(link)
            
            if items:
                print(f"✅ {name} 成功透過代理抓到 {len(items)} 則")
                summary_text += f"\n<b>【{name} ({len(items)}則)】</b>\n" + "\n".join(items) + "\n"
        except Exception as e:
            print(f"❌ {name} 代理過程出錯: {str(e)}")

    if summary_text:
        tw_now = (now_utc + timedelta(hours=8)).strftime('%m/%d %H:%M')
        final_msg = f"<b>▋ 深度新聞巡邏 ({tw_now})</b>\n" + summary_text
        send_to_telegram(final_msg)
        
        # 存回紀錄檔，實現跨媒體去重
        with open(history_file, "a") as f:
            for l in new_found_links:
                f.write(l + "\n")
    else:
        print("最終結果：中繼抓取成功，但目前無新新聞。")

if __name__ == "__main__":
    main()
