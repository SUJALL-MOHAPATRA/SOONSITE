from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
import json
import os
from scheduler import run_scheduler
import threading

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "fallback_secret")
app.config['SESSION_PERMANENT'] = False

DATA_FILE = 'data.json'
SITE_NAME = 'SOONSITE'

# Data loading from JSON data file
def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

# Data saving to JSON data file
def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

EMAILS_FILE = 'emails.json'

def load_emails():
    if not os.path.exists(EMAILS_FILE):
        with open(EMAILS_FILE, 'w') as f:
            json.dump([], f)
    with open(EMAILS_FILE, 'r') as f:
        return json.load(f)

def save_emails(emails):
    with open(EMAILS_FILE, 'w') as f:
        json.dump(emails, f, indent=4)

# --------- AUTH ROUTES ---------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'TERMIN8R' and password == 'Avenger24680':   # hardcoded login
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            return 'Invalid credentials', 401
    return render_template('login.html', site_name=SITE_NAME)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.clear()
    return redirect(url_for('index'))

# --------- MAIN PAGES ---------
@app.route('/')
def index():
    data = load_data()
    today = datetime.today().date()
    # Filtering past releases
    upcoming = [item for item in data if datetime.strptime(item['release_date'], "%Y-%m-%d").date() >= today]
    # Sorting by release date
    upcoming.sort(key=lambda x: datetime.strptime(x['release_date'], "%Y-%m-%d").date())

    # Format date for display
    for item in upcoming:
        dt = datetime.strptime(item['release_date'], "%Y-%m-%d")
        item['formatted_date'] = dt.strftime("%d %B %Y")  # 2-digit day, full month, year

    save_data(upcoming)  #Filtered data saved

    return render_template('index.html', items=upcoming, site_name=SITE_NAME)

@app.route('/add', methods=['GET', 'POST'])
def add():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        type_ = request.form['type']
        release_date = request.form['release_date']
        link_texts = request.form.getlist('link_text[]')
        link_urls = request.form.getlist('link_url[]')

        links = [
            {"text": text, "url": url}
            for text, url in zip(link_texts, link_urls)
            if text.strip() and url.strip()
        ]

        data = load_data()
        dt = datetime.strptime(release_date, "%Y-%m-%d")
        formatted_date = dt.strftime("%d %B %Y")

        data.append({
            'title': title,
            'type': type_,
            'release_date': release_date,
            'links': links,
            'formatted_date': formatted_date,
            'notified': False
        })
        save_data(data)
        return redirect(url_for('index'))
    return render_template('add.html', site_name=SITE_NAME)

@app.route('/delete/<int:i>', methods=['POST'])
def delete(i):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    items = load_data()
    if 0 <= i < len(items):
        items.pop(i)
        save_data(items)
    return redirect(url_for('index'))

@app.route('/change/<int:i>', methods=['GET', 'POST'])
def change(i):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    items = load_data()

    if request.method == 'POST':
        title = request.form.get('title')
        item_type = request.form.get('type')
        release_date = request.form.get('release_date')
        link_texts = request.form.getlist('link_text[]')
        link_urls = request.form.getlist('link_url[]')

        if title and item_type and release_date:
            links = [
                {"text": text, "url": url}
                for text, url in zip(link_texts, link_urls)
                if text.strip() and url.strip()
            ]
            items[i] = {
                'title': title,
                'type': item_type,
                'release_date': release_date,
                'links': links
            }
            save_data(items)
            return redirect(url_for('index'))
        else:
            return "Missing form data", 400

    return render_template('change.html', item=items[i], index=i, site_name=SITE_NAME)

@app.route('/emails', methods=['GET', 'POST'])
def manage_emails():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    emails = load_emails()
    if request.method == 'POST':
        new_emails = request.form.get('new_email')
        if new_emails:
            for email in [e.strip() for e in new_emails.split(',') if e.strip()]:
                if email not in emails:
                    emails.append(email)
            save_emails(emails)
        return redirect(url_for('manage_emails'))

    return render_template('emails.html', emails=emails, site_name=SITE_NAME)

@app.route('/emails/delete/<email>', methods=['POST'])
def delete_email(email):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    emails = load_emails()
    emails = [e for e in emails if e != email]
    save_emails(emails)
    return redirect(url_for('manage_emails'))

if __name__ == '__main__':
    # Start scheduler in a background thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

    # Start Flask app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

