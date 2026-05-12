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
        # 自動檢查並修正常見的網址門牌錯誤
        test_url = url
        if name == "中時新聞" and "www." not in url:
            test_url = url.replace("https://", "https://www.")
        if name == "自由時報" and "news." not in url:
            test_url = url.replace("https://", "https://news.")
        if name == "教育電台" and not url.endswith("current"):
            test_url = "https://ner.gov.tw"

        print(f"DEBUG: 正在嘗試存取 {name}，網址: {test_url}")
        
        try:
            # 身份偽裝更徹底
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                'Referer': 'https://google.com'
            }
            resp = requests.get(test_url, headers=headers, timeout=20, verify=False)
            print(f"DEBUG: {name} 狀態碼: {resp.status_code}")
            
            feed = feedparser.parse(resp.content)
            items = []
            
            # --- 核心改動：直接抓取所有 entries，不設任何時間或則數限制 ---
            for entry in feed.entries:
                link = getattr(entry, 'link', None)
                if not link or link in seen_links: continue
                
                items.append(f"• <a href='{link}'>{entry.title}</a>")
                seen_links.add(link)
            
            if items:
                summary_text += f"<b>【{name} ({len(items)}則)】</b>\n" + "\n".join(items) + "\n\n"
                has_news = True
                print(f"DEBUG: {name} 成功抓到 {len(items)} 則")
            else:
                print(f"DEBUG: {name} 內容為空 (可能被阻擋或解析失敗)")
        except Exception as e:
            print(f"DEBUG: {name} 發生連線錯誤: {str(e)[:50]}")



    if has_news:
        send_to_telegram(summary_text)
    else:
        send_to_telegram("📢 目前無新內容")


if __name__ == "__main__":
    # 忽略教育電台可能產生的 SSL 安全警告
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    main()
