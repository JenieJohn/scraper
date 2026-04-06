import requests
from bs4 import BeautifulSoup
import time
import smtplib
from email.message import EmailMessage

# Configuration
URL = "https://www.bseindia.com/corporates/ann.html"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Referer": "https://www.bseindia.com/"
}
TELEGRAM_TOKEN = "8627907721:AAHvNWqc1SAPmdR9MU1jCw29VuNnIueCL2g"  
TELEGRAM_CHAT_ID = "53589388"           

def fetch_announcements():
    try:
        response = requests.get(URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract announcements (update selector based on actual page structure)
        announcements = []
        table = soup.find('table', {'id': 'announcementTable'})  # Hypothetical table ID
        if table:
            for row in table.find_all('tr')[1:]:  # Skip header
                cols = row.find_all('td')
                if len(cols) >= 4:
                    announcements.append({
                        "company": cols[0].text.strip(),
                        "title": cols[1].text.strip(),
                        "date": cols[2].text.strip(),
                        "link": cols[1].find('a')['href'] if cols[1].find('a') else None
                    })
        return announcements
    except Exception as e:
        print(f"Error fetching data: {e}")
        return []

def send_alert(subject, body):
    message = f"*{subject}*\n\n{body}"  # Format as Markdown
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": 53589388,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print("Telegram alert sent!")
        else:
            print(f"Failed to send Telegram alert: {response.text}")
    except Exception as e:
        print(f"Error sending Telegram alert: {e}")

def monitor(interval=3600):
    last_announcements = []
    while True:
        print("Checking for new announcements...")
        current_announcements = fetch_announcements()
        
        if last_announcements:
            new_announcements = [ann for ann in current_announcements if ann not in last_announcements]
            if new_announcements:
                alert_body = "\n".join([f"{ann['company']}: {ann['title']} ({ann['date']})" for ann in new_announcements])
                send_alert("New BSE Announcements Alert!", alert_body)
        
        last_announcements = current_announcements.copy()
        time.sleep(interval)

if __name__ == "__main__":
    monitor()  # Check every hour