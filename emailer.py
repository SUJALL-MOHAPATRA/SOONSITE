import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import json
import os

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

DATA_FILE = "data.json"
EMAILS_FILE = "emails.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w') as f:
            json.dump([], f)
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load_emails():
    if not os.path.exists(EMAILS_FILE):
        with open(EMAILS_FILE, 'w') as f:
            json.dump([], f)
    with open(EMAILS_FILE, 'r') as f:
        return json.load(f)

def send_email(subject, body):
    from_addr = SENDER_EMAIL
    recipients = load_emails()

    if not recipients:
        print("No recipients found in emails.json.")
        return

    msg = MIMEMultipart()
    msg['From'] = from_addr
    msg['To'] = "Undisclosed Recipients"
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(from_addr, recipients, msg.as_string())
        print(f"Email sent to {len(recipients)} recipient(s).")
    except Exception as e:
        print(f"Error sending email: {e}")

def check_and_send():
    data = load_data()
    today = datetime.today().date()
    changed = False

    for item in data:
        release_date = datetime.strptime(item["release_date"], "%Y-%m-%d").date()
        days_left = (release_date - today).days

        if not item.get("notified", False):
            subject = f"Reminder: '{item['title']}' is releasing soon!"
            body = (
                f"Don't forget!\n\n"
                f"Title: {item['title']}\n"
                f"Type: {item['type']}\n"
                f"Release Date: {item['release_date']}\n\n"
                f"Links:\n" +
                "\n".join(f"{link['text']}: {link['url']}" for link in item.get("links", []))
            )

            send_email(subject, body)
            item["notified"] = True
            changed = True

    if changed:
        save_data(data)

if __name__ == "__main__":
    check_and_send()
