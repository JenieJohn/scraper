import requests
import time

# --- CONFIGURATION ---
TELEGRAM_BOT_TOKEN = "7653009328:AAG7wwITnjXZOo8g_RP4JhnJ8fL50lvIzg0"
TELEGRAM_CHAT_ID = "53589388"
# API for Corporate Announcements
BSE_API_URL = "https://api.bseindia.com/BseIndiaAPI/ServiceData/CorpAnnouncementData.aspx?typ=A&cat=-1&prev=1"

# Mimic a real Chrome Browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Referer": "https://www.bseindia.com/corporates/ann.html",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://www.bseindia.com",
}

# Use a Session to persist cookies
session = requests.Session()
session.headers.update(HEADERS)

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    try:
        req = session.post(url, json=payload, timeout=10)
        return req.json()
    except Exception as e:
        print(f"Telegram Error: {e}")

def fetch_announcements():
    try:
        # First, hit the main page to get any necessary session cookies
        session.get("https://www.bseindia.com", timeout=10)
        
        # Now fetch the actual data
        response = session.get(BSE_API_URL, timeout=15)
        
        if response.status_code == 200:
            # Attempt to parse JSON
            return response.json()
        else:
            print(f"BSE Server blocked request. Status Code: {response.status_code}")
            return []
    except ValueError:
        print("❌ BSE returned HTML instead of JSON (Bot Detection Triggered).")
        return []
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return []

# Tracking variable
last_processed_id = None

print("🚀 BSE Monitoring Bot is running...")
print("Press Ctrl+C to stop.")

while True:
    data = fetch_announcements()
    
    if data and isinstance(data, list):
        latest = data[0]
        current_id = latest.get("NEWS_ID")

        # Check if this is a new announcement
        if last_processed_id != current_id:
            company = latest.get("SLONGNAME", "N/A")
            category = latest.get("CATEGORYNAME", "General")
            subject = latest.get("NEWSSUB", "No Subject")
            attachment = latest.get("ATTACHMENTNAME", "")
            
            # Construct PDF link
            pdf_link = f"https://www.bseindia.com/xml-data/corpfiling/AttachLive/{attachment}" if attachment else "No Document Available"

            message = (
                f"🔔 *New BSE Announcement*\n\n"
                f"*Stock:* {company}\n"
                f"*Type:* {category}\n"
                f"*Subject:* {subject}\n\n"
                f"🔗 [View Official Document]({pdf_link})"
            )
            
            send_telegram_message(message)
            last_processed_id = current_id
            print(f"✅ Alert sent: {company} - {current_id}")
    else:
        print("Waiting for data/No new updates...")

    # Wait 2 minutes between checks to avoid IP banning
    time.sleep(120)