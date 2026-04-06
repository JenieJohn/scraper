#perfect condition though needs some modification but keep this as org source


import requests
import time
import os

# --- CONFIG ---
BOT_TOKEN = "8627907721:AAHvNWqc1SAPmdR9MU1jCw29VuNnIueCL2g"
CHAT_ID = "53589388"
CHECK_INTERVAL = 5 

seen_ids = set()

def escape_html(text):
    """Prevents Telegram from crashing on special characters like & or <"""
    if not text: return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    try:
        response = requests.post(url, data=payload, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Telegram Error: {e}")

def get_bse_announcements():
    # Note: Use the 'CorporateAnn.aspx' endpoint if the SubCategory one times out
    url = "https://api.bseindia.com/BseIndiaAPI/api/AnnSubCategoryGetData/w"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.bseindia.com/",
        "Origin": "https://www.bseindia.com"
    }

    params = {
        "pageno": 1,
        "strCat": "-1",
        "strPrevDate": "",
        "strScrip": "",
        "strSearch": "P",
        "strToDate": "",
        "strType": "C",
        "subcategory": "-1"
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=20)
        
        # Check if we got HTML (blocked) instead of JSON
        if "application/json" not in response.headers.get("Content-Type", ""):
            print("⚠️ BSE returned HTML (Request likely blocked). Retrying later...")
            return []

        data = response.json()
        return data.get("Table", [])

    except Exception as e:
        print(f"⚠️ BSE Fetch Error: {e}")
        return []

def format_message(item):
    # Escape HTML to prevent Telegram parsing errors
    title = escape_html(item.get("HEADLINE", "No Title"))
    company = escape_html(item.get("SLONGNAME", "Unknown Company"))
    date = item.get("NEWS_DT", "N/A")
    link = item.get("ATTACHMENTNAME", "")

    pdf_url = f"https://www.bseindia.com/xml-data/corpfiling/AttachLive/{link}"

    return (
        f"📢 <b>BSE Announcement</b>\n\n"
        f"🏢 <b>{company}</b>\n"
        f"📝 {title}\n"
        f"📅 {date}\n\n"
        f"🔗 <a href='{pdf_url}'>View Full PDF Report</a>"
    )

def main():
    print("🚀 BSE Scraper Active...")
    global seen_ids
    
    # Track if we have performed the initial population of IDs
    is_initialized = False

    while True:
        announcements = get_bse_announcements()

        if announcements:
            if not is_initialized:
                # Store all current IDs so we only alert on NEW ones later
                for item in announcements:
                    seen_ids.add(item.get("NEWSID"))
                is_initialized = True
                print(f"✅ Initialized with {len(seen_ids)} existing records. Monitoring for news...")
            else:
                for item in announcements:
                    news_id = item.get("NEWSID")

                    if news_id not in seen_ids:
                        print(f"🆕 New Announcement: {item.get('HEADLINE')}")
                        message = format_message(item)
                        send_telegram(message)
                        seen_ids.add(news_id)
                        
                        # Prevent the set from growing too large over weeks
                        if len(seen_ids) > 1000:
                            seen_ids.clear() # Simplest way to reset; next run re-initializes
                            is_initialized = False 
        else:
            print("⏳ No data received (Server busy or no results).")

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()