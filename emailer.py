import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import os

# ---------------- Database Config ----------------
def get_db_connection():
    return psycopg2.connect(
        dbname=os.environ.get("DB_NAME"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        host=os.environ.get("DB_HOST"),
        port=os.environ.get("DB_PORT)
    )
# ---------------- Email Config ----------------
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")

# ---------------- Load Data from Database ----------------
def load_data():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Fetch projects
    cur.execute("SELECT id, title, type, release_date, notified FROM projects ORDER BY release_date;")
    projects = cur.fetchall()

    # For each project, fetch links
    for project in projects:
        cur.execute("SELECT link_id, link_url, link_text FROM project_links WHERE project_id = %s;", (project["id"],))
        project["links"] = cur.fetchall()

    cur.close()
    conn.close()
    return projects

# ---------------- Save Data back to Database ----------------
def save_data(data):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    for item in data:
        # Update notified flag
        cur.execute(
            "UPDATE projects SET notified = %s WHERE id = %s;",
            (item.get("notified", False), item["id"])
        )

    conn.commit()
    cur.close()
    conn.close()

# ---------------- Load Emails from Database ----------------
def load_emails():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT email FROM rec_emails;")
    mails = [row["email"] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return mails

# ---------------- Email Sending ----------------
def send_email(subject, body):
    from_addr = SENDER_EMAIL
    recipients = load_emails()

    if not recipients:
        print("No recipients found in database.")
        return

    # Create email
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

# ---------------- Check & Send Reminder ----------------
def mark_as_notified(project_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE projects SET notified = TRUE WHERE id = %s;", (project_id,))
    conn.commit()
    cur.close()
    conn.close()

def check_and_send():
    data = load_data()
    today = datetime.today().date()
    changed = False

    for item in data:
        # Convert release_date from datetime/date to date
        if isinstance(item["release_date"], str):
            release_date = datetime.strptime(item["release_date"], "%Y-%m-%d").date()
        else:
            release_date = item["release_date"]

        days_left = (release_date - today).days

        if days_left <= 10 and not item.get("notified", False):
            subject = f"Reminder: '{item['title']}' is releasing in {days_left} days!"
            body = (
                f"Don't forget!\n\n"
                f"Title: {item['title']}\n"
                f"Type: {item['type']}\n"
                f"Release Date: {release_date.strftime('%Y-%m-%d')}\n\n"
                f"Links:\n" +
                "\n".join(f"{link['text']}: {link['url']}" for link in item.get("links", []))
            )

            send_email(subject, body)

            # Update notified flag in DB immediately
            mark_as_notified(item["id"])
            changed = True

    if not changed:
        print("No new reminders to send.")

# ---------------- Main ----------------
if __name__ == "__main__":
    check_and_send()
