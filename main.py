# -*- coding: utf-8 -*-
import time, os, requests, feedparser, urllib3
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HISTORY_FILE = "last_run_time.txt"
# 這是你網頁的固定標題
REPORT_FILE = "index.html"

def get_last_run_time():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            try: return datetime.strptime(f.read().strip(), "%Y-%m-%d %H:%M:%S")
            except: pass
    return datetime.now() - timedelta(hours=2)

def save_current_run_time(latest_time):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        f.write(latest_time.strftime("%Y-%m-%d %H:%M:%S"))

# 抓取邏輯 (使用 Requests 代替 Selenium 以確保雲端穩定執行)
def fetch_news(name, url, start_time):
    res = []
    headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15'}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        # 這裡是通用的標題抓取邏輯，確保能抓到多報社
        items = soup.select('ul.vertical-list > li, .article-list .col, #jsMainList li, .story-list__text')
        for art in items:
            t_tag = art.select_one('a')
            d_tag = art.select_one('time, .date')
            if not t_tag or not d_tag: continue
            
            href = t_tag.get('href', '')
            if not href.startswith('http'): href = "https://chinatimes.com" + href # 範例補全
            
            title = t_tag.text.strip()
            # 簡化時間判定，若抓不到具體時間則跳過 (確保穩定)
            res.append((datetime.now(), title, href)) 
    except: pass
    return res

def fetch_ltn_rss(start_time):
    res = []; seen = set()
    for ch in ["all", "politics"]:
        try:
            feed = feedparser.parse(f"https://ltn.com.tw{ch}.xml")
            for e in feed.entries:
                dt = datetime(*(e.published_parsed[0:6])) + timedelta(hours=8)
                if dt >= start_time and e.link not in seen:
                    seen.add(e.link); res.append((dt, e.title, e.link))
        except: continue
    return res

def main():
    last_run_ts = get_last_run_time()
    all_res = fetch_ltn_rss(last_run_ts) # 先以自由時報為例，可擴充
    
    if all_res:
        all_res.sort(key=lambda x: x[0], reverse=True)
        # 生成大字體 HTML
        now_str = datetime.now().strftime('%m/%d %H:%M')
        html = f"""<html><head><meta charset='utf-8'><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: sans-serif; padding: 15px; background: #f4f4f4; }}
            .item {{ background: #fff; padding: 20px; margin-bottom: 10px; border-radius: 8px; border-left: 8px solid #004a99; }}
            .time {{ color: #e74c3c; font-weight: bold; font-size: 18px; }}
            .title {{ display: block; text-decoration: none; color: #111; font-size: 26px; font-weight: bold; margin-top: 5px; }}
            .footer {{ text-align: center; color: #888; font-size: 14px; margin-top: 20px; }}
        </style></head><body>
        <h1>新聞巡邏 {now_str}</h1>"""
        
        for dt, title, url in all_res:
            html += f"<div class='item'><span class='time'>{dt.strftime('%H:%M')}</span><a class='title' href='{url}'>{title}</a></div>"
        
        html += "<div class='footer'>更新於 " + now_str + "</div></body></html>"
        
        with open(REPORT_FILE, "w", encoding="utf-8") as f:
            f.write(html)
        
        save_current_run_time(all_res[0][0])
        print(f"成功更新 {len(all_res)} 則新聞")
    else:
        print("沒有新新聞")

if __name__ == "__main__":
    main()
