import requests
import time
from datetime import datetime
import os

# --- CONFIGURATION ---
# IMPORTANT: Ensure you have revoked your previous token via @BotFather!
TELEGRAM_TOKEN = "8627907721:AAHvNWqc1SAPmdR9MU1jCw29VuNnIueCL2g"
CHAT_ID = "53589388"
CHECK_INTERVAL = 2  # 5 minutes
DB_FILE = "sent_ids.txt"

BSE_URL = "https://www.bseindia.com/corporates/ann.html"

# Enhanced Session with browser-like headers to prevent timeouts/blocks
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.bseindia.com/",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://www.bseindia.com",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site"
})

# Load previously sent IDs from file
if os.path.exists(DB_FILE):
    with open(DB_FILE, "r") as f:
        sent_announcements = set(line.strip() for line in f)
else:
    sent_announcements = set()

def save_id(news_id):
    """Saves a new ID to the tracking set and the local file."""
    sent_announcements.add(news_id)
    with open(DB_FILE, "a") as f:
        f.write(f"{news_id}\n")

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        session.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"Telegram Error: {e}")

def fetch_announcements():
    # Using specific dates helps the API respond faster
    today = datetime.now().strftime('%d%m%Y')
    params = {
        "cat": "Result", 
        "prevDate": today, 
        "scrip": "", 
        "startDate": today, 
        "endDate": today
    }
    
    # Retry Logic (Tries up to 3 times if server times out)
    for attempt in range(3):
        try:
            print(f"Fetching data (Attempt {attempt + 1})...")
            # Increased timeout to 30 seconds
            response = session.get(BSE_URL, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            table = data.get('Table', [])
            
            if not table:
                print("No new results found.")
                return

            for entry in table:
                news_id = str(entry.get('NEWSID'))
                
                if news_id not in sent_announcements:
                    company_name = entry.get('SLONGNAME')
                    date_time = entry.get('NEWS_DT')
                    pdf_link = entry.get('ATTACHMENTNAME')
                    
                    full_pdf_url = f"https://www.bseindia.com/xml-data/corpfiling/AttachLive/{pdf_link}"
                    
                    message = (
                        f"🔔 *New Financial Result*\n\n"
                        f"🏢 *Company:* {company_name}\n"
                        f"📅 *Time:* {date_time}\n"
                        f"🔗 [View PDF Results]({full_pdf_url})"
                    )
                    
                    send_telegram_msg(message)
                    save_id(news_id)
                    print(f"Sent notification for: {company_name}")
            
            break # Success! Exit the retry loop.

        except requests.exceptions.Timeout:
            print("Server timed out. Waiting 10s before retry...")
            time.sleep(10)
        except Exception as e:
            print(f"Critical Error: {e}")
            break

if __name__ == "__main__":
    print("Scraper started...")
    while True:
        fetch_announcements()
        print(f"Waiting {CHECK_INTERVAL} seconds for next check...")
        time.sleep(CHECK_INTERVAL)