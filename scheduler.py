# scheduler.py
import schedule
import time
import subprocess
import threading

def send_emails():
    print("Running emailer.py...")
    subprocess.run(["python", "emailer.py"])

def run_scheduler():
    # Schedule jobs
    schedule.every().day.at("06:00").do(send_emails)
    print("Scheduler started. Waiting for tasks...")

    while True:
        schedule.run_pending()
        time.sleep(60)
