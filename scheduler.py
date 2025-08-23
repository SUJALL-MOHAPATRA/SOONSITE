import schedule
import time
import subprocess
import os
os.system("notepad.exe")

#Run emailer.py
def send_emails():
    print("Running emailer.py...")
    subprocess.run(["python", "emailer.py"])

#Schedule the job
schedule.every().day.at("6:00").do(send_emails)

print("Scheduler started. Waiting for tasks...")

while True:
    schedule.run_pending()
    time.sleep(60)
