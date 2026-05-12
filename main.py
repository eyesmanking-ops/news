# -*- coding: utf-8 -*-
import os, requests, feedparser, time
from datetime import datetime, timedelta

def send_to_telegram(text):
    token = os.getenv("TG_TOKEN")
    chat_id = os.getenv("TG_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    # 如果內容超過 3500 字，自動拆分發送
    if len(text) > 3500:
        print("DEBUG: 內容過長，分段發送...")
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
        resp = requests.post(url, data={"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True})
        print(f"DEBUG: Telegram 回應: {resp.text}")




def main():
    print("DEBUG: 程式開始執行")
    
    # 這裡我們用「基礎網址 + 後綴」的方式，避免系統縮址問題
    # 採用零件拼湊法，徹底避開系統縮網址問題
    # 程式執行時會自動組合成：https:// + 網域 + 路徑
    SOURCES = {
        "中央社": "https://feeds.feedburner.com/rsscna/mainland",
        "自由時報": "https://news.ltn.com.tw/rss/all.xml",
        "中時新聞": "https://www.chinatimes.com/rss/realtimenews-total.xml",
        "聯合新聞": "https://udn.com/rssfeed/news/2/6638?ch=news",
        "青年日報": "https://www.ydn.com.tw/rss/news/1",
        "教育電台": "https://www.ner.gov.tw/rss"
    }

    
    # 模擬成高權限的電腦版 Chrome 瀏覽器，這比手機版更難被阻擋
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }

    
    summary_text = f"<b>▋ 新聞巡邏 ({datetime.now().strftime('%m/%d %H:%M')})</b>\n\n"
    has_news = False

    for name, url in SOURCES.items():
        try:
            # 關鍵：加上 Referer 偽裝和忽略安全檢查
            headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15',
                'Referer': 'https://google.com'
            }
            # verify=False 是為了救回教育電台
            resp = requests.get(url, headers=headers, timeout=20, verify=False)
            resp.encoding = 'utf-8'
            feed = feedparser.parse(resp.text)
            print(f"DEBUG: {name} 抓取狀態碼: {resp.status_code}")
            print(f"DEBUG: {name} 解析到的則數: {len(feed.entries)}")

            
            items = []
            # 改為 125 分鐘，確保跨小時不遺漏
            time_limit = datetime.utcnow() - timedelta(minutes=125)
            
            for entry in feed.entries:
                link = getattr(entry, 'link', None)
                if not link or link in seen_links: continue
                
                # --- 暫時註解掉時間判定，確保所有抓到的都顯示出來 ---
                items.append(f"• <a href='{link}'>{entry.title}</a>")
                seen_links.add(link)

                
                pub_time = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_time = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                
                # 確保是兩小時內的
                if pub_time is None or pub_time > time_limit:
                    items.append(f"• <a href='{link}'>{entry.title}</a>")
                    seen_links.add(link)
            
            if items:
                summary_text += f"<b>【{name}】</b>\n" + "\n".join(items) + "\n\n"
                has_news = True
        except:
            continue


    if has_news:
        send_to_telegram(summary_text)
    else:
        send_to_telegram("📢 目前無新內容")


if __name__ == "__main__":
    # 忽略教育電台可能產生的 SSL 安全警告
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    main()
