# -*- coding: utf-8 -*-
import os, requests, feedparser
from datetime import datetime, timedelta

def send_to_telegram(text):
    # 使用您在 GitHub Secrets 設定的正確名稱
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("❌ 錯誤：Python 抓不到環境變數。請檢查 run.yml 是否有正確對接變數。")
        return

    # Telegram API 標準格式 (bot+token)
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    
    try:
        resp = requests.post(url, data=payload, timeout=20)
        if resp.status_code == 200:
            print("✅ Telegram 傳送成功！")
        else:
            print(f"❌ 傳送失敗，狀態碼: {resp.status_code}，回應: {resp.text}")
    except Exception as e:
        print(f"⚠️ 連線異常: {e}")

def main():
    SOURCES = {
        "中央社-政治": "https://feeds.feedburner.com/rsscna/politics",
        "中央社-社會": "https://feeds.feedburner.com/rsscna/social",
        "中央社-兩岸": "https://feeds.feedburner.com/rsscna/mainland",
        "自由時報-全部": "https://news.ltn.com.tw/rss/all.xml"
    }
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    # 設定抓取 45 分鐘內的新聞 (配合 30 分鐘跑一次的頻率)
    now_utc = datetime.utcnow()
    time_threshold = now_utc - timedelta(minutes=45)
    
    tw_now_str = (now_utc + timedelta(hours=8)).strftime('%m/%d %H:%M')
    summary_text = f"<b>▋ 新聞巡邏 ({tw_now_str})</b>\n"
    has_news = False

    for name, url in SOURCES.items():
        try:
            resp = requests.get(url, headers=headers, timeout=30)
            feed = feedparser.parse(resp.content)
            items = []
            for entry in feed.entries:
                try:
                    pub_time = datetime(*entry.published_parsed[:6])
                    if pub_time > time_threshold:
                        tw_time = (pub_time + timedelta(hours=8)).strftime('%H:%M')
                        items.append(f"• [{tw_time}] <a href='{entry.link}'>{entry.title}</a>")
                except:
                    continue
            
            if items:
                summary_text += f"\n<b>【{name} ({len(items)}則)】</b>\n" + "\n".join(items) + "\n"
                has_news = True
        except:
            continue

    if has_news:
        send_to_telegram(summary_text)
    else:
        print("此時段無新新聞。")

if __name__ == "__main__":
    main()
