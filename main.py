# -*- coding: utf-8 -*-
import os, requests, feedparser
from datetime import datetime, timedelta

def send_to_telegram(text):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("❌ 錯誤：找不到環境變數")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    # --- 僅在此處加入切分邏輯，其餘連線參數完全不動 ---
    # 設定 3500 字為安全門檻
    if len(text) > 3500:
        # 以您的媒體大標題格式作為切分點
        parts = text.split('\n<b>【') 
        current_msg = parts[0]
        
        for i in range(1, len(parts)):
            next_part = '\n<b>【' + parts[i]
            # 如果累積字數即將超標，就先發出目前這一段
            if len(current_msg) + len(next_part) > 3500:
                payload = {
                    "chat_id": chat_id,
                    "text": current_msg,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True
                }
                requests.post(url, data=payload, timeout=20)
                # 重置下一段訊息的開頭
                current_msg = "<b>▋ 新聞巡邏 (續)</b>\n" + next_part
            else:
                current_msg += next_part
        
        # 發送最後剩餘的內容
        final_payload = {
            "chat_id": chat_id,
            "text": current_msg,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        resp = requests.post(url, data=final_payload, timeout=20)
        print(f"Telegram 最終分段回應: {resp.status_code}")
        
    else:
        # 字數正常時，執行您原本成功的發送代碼
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        try:
            resp = requests.post(url, data=payload, timeout=20)
            print(f"Telegram 回應: {resp.status_code}")
        except Exception as e:
            print(f"發送失敗: {e}")

def main():
    SOURCES = {
        "中央社-政治": "https://feeds.feedburner.com/rsscna/politics",
        "中央社-社會": "https://feeds.feedburner.com/rsscna/social",
        "中央社-兩岸": "https://feeds.feedburner.com/rsscna/mainland",
        "中央社-即時": "https://feeds.feedburner.com/rsscna/main",
        "中央社-產經": "https://feeds.feedburner.com/rsscna/finance",
        "自由時報-全部": "https://news.ltn.com.tw/rss/all.xml"
    }
    
    # 讀取歷史紀錄，避免重複推播
    history_file = "sent_links.txt"
    sent_links = set()
    if os.path.exists(history_file):
        with open(history_file, "r") as f:
            sent_links = set(f.read().splitlines())

    # 設定抓取範圍：過去 12 小時內
    now_utc = datetime.utcnow()
    time_threshold = now_utc - timedelta(hours=12)
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    summary_text = ""
    new_found_links = []

    for name, url in SOURCES.items():
        try:
            resp = requests.get(url, headers=headers, timeout=30)
            feed = feedparser.parse(resp.content)
            items = []
            
            for entry in feed.entries:
                link = entry.link
                # 判定條件：沒發送過 且 在時間範圍內
                if link not in sent_links:
                    try:
                        # 解析 RSS 內的時間
                        pub_time = datetime(*entry.published_parsed[:6])
                        if pub_time > time_threshold:
                            tw_time = (pub_time + timedelta(hours=8)).strftime('%H:%M')
                            items.append(f"• [{tw_time}] <a href='{link}'>{entry.title}</a>")
                            new_found_links.append(link)
                    except:
                        continue
            
            if items:
                summary_text += f"\n<b>【{name} ({len(items)}則)】</b>\n" + "\n".join(items) + "\n"
        except Exception as e:
            print(f"{name} 抓取異常: {e}")

    if summary_text:
        tw_now = (now_utc + timedelta(hours=8)).strftime('%m/%d %H:%M')
        final_msg = f"<b>▋ 新聞巡邏 ({tw_now})</b>\n" + summary_text
        send_to_telegram(final_msg)
        
        # 更新歷史紀錄檔 (保留最近 1000 筆即可)
        updated_history = list(sent_links) + new_found_links
        with open(history_file, "w") as f:
            f.write("\n".join(updated_history[-1000:]))
        print(f"✅ 發現 {len(new_found_links)} 則新新聞，已更新紀錄。")
    else:
        print("💡 目前無新新聞。")

if __name__ == "__main__":
    main()
