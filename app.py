from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime, date
import psycopg2
from psycopg2.extras import RealDictCursor
import os

SITE_NAME = 'SOONSITE'

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev_secret")
app.config['SESSION_PERMANENT'] = False

def get_db_connection():
    conn = psycopg2.connect(
        host=os.environ.get("DB_HOST"),
        database=os.environ.get("DB_NAME"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        port=os.environ.get("DB_PORT")
    )
    return conn

def delete_expired_projects():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    today = date.today()

    cur.execute("DELETE FROM projects WHERE release_date < %s;", (today,))
    conn.commit()
    cur.close()
    conn.close()

def load_data():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Fetch all projects
    cur.execute("""
        SELECT id, title, type, release_date, formatted_date, notified 
        FROM projects
        ORDER BY release_date ASC;
    """)
    projects = cur.fetchall()

    result = []
    for project in projects:
        id_ = project['id']

        # Fetch related links for this project
        cur.execute("""
            SELECT link_text, link_url 
            FROM project_links 
            WHERE project_id = %s;
        """, (id_,))
        links = cur.fetchall()
        link_list = [{"text": text, "url": url} for text, url in links]

        result.append({
            "id": project['id'],
            "title": project['title'],
            "type": project['type'],
            "release_date": project['release_date'].strftime("%Y-%m-%d"),
            "formatted_date": project['formatted_date'],
            "notified": project['notified'],
            "links": link_list
        })

    cur.close()
    conn.close()
    return result

def save_data(data_list):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    for project in data_list:
        # Ensure project is a plain dict (avoid RealDictRow issues)
        project = dict(project)

        # Insert or update project
        cur.execute("""
            INSERT INTO projects (title, type, release_date, formatted_date, notified)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (title) DO UPDATE
            SET type = EXCLUDED.type,
                release_date = EXCLUDED.release_date,
                formatted_date = EXCLUDED.formatted_date,
                notified = EXCLUDED.notified;
        """, (
            project['title'],
            project['type'],
            project['release_date'],
            project['formatted_date'],
            project['notified']
        ))

        # Get project ID
        cur.execute("SELECT id FROM projects WHERE title = %s;", (project['title'],))
        id_ = cur.fetchone()['id']  # RealDictRow → use key access

        # Clear existing links to prevent duplicates
        cur.execute("DELETE FROM project_links WHERE project_id = %s;", (id_,))

        # Insert links if any
        for link in project['links']:
            link = dict(link)  # Convert to normal dict if it’s a RealDictRow
            cur.execute("""
                INSERT INTO project_links (project_id, link_text, link_url)
                VALUES (%s, %s, %s);
            """, (id_, link['text'], link['url']))

    conn.commit()
    cur.close()
    conn.close()

def load_emails():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT email FROM rec_emails;")
    mails = [row["email"] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return mails

def save_emails(emails):
    conn = get_db_connection()
    cur = conn.cursor()
    for mail in emails:
        cur.execute(
            "INSERT INTO rec_emails (email) VALUES (%s) ON CONFLICT (email) DO NOTHING;",
            (mail,)
        )
    conn.commit()
    cur.close()
    conn.close()

# --------- AUTH ROUTES ---------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == os.environ.get("USER_NAME") and password == os.environ.get("USER_PASS"):   # hardcoded login
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
    delete_expired_projects()
    today = date.today()

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Get projects
    cur.execute("""
        SELECT id, title, type, release_date, formatted_date, notified
        FROM projects
        ORDER BY release_date;
    """)
    projects = cur.fetchall()

    # Get all links
    cur.execute("""
        SELECT project_id, link_text, link_url
        FROM project_links;
    """)
    all_links = cur.fetchall()
    cur.close()
    conn.close()

    # Attach links to projects
    for project in projects:
        project["links"] = [
            {"link_text": l["link_text"], "link_url": l["link_url"]}
            for l in all_links if l["project_id"] == project["id"]
        ]

    # Filter only upcoming projects
    upcoming = []
    for project in projects:
        dt = project["release_date"]
        if isinstance(dt, str):
            dt = datetime.strptime(dt, "%Y-%m-%d").date()
        if dt >= today:
            upcoming.append(project)

    # Sort by release date
    upcoming.sort(key=lambda x: x["release_date"])

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
            {"text": str(text), "url": str(url)}
            for text, url in zip(link_texts, link_urls)
            if text.strip() and url.strip()
        ]

        # Format date for display
        dt = datetime.strptime(release_date, "%Y-%m-%d")
        formatted_date = dt.strftime("%d %B %Y")

        # Insert into DB
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Insert project
        cur.execute("""
            INSERT INTO projects (title, type, release_date, formatted_date, notified)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id;
        """, (title, type_, release_date, formatted_date, False))
        id_row = cur.fetchone()
        id_ = id_row['id']  # RealDictRow → key access

        # Insert links if any
        for link in links:
            link = dict(link)  # Ensure it's a plain dict
            cur.execute("""
                INSERT INTO project_links (project_id, link_text, link_url)
                VALUES (%s, %s, %s);
            """, (id_, link['text'], link['url']))

        conn.commit()
        cur.close()
        conn.close()

        return redirect(url_for('index'))
    return render_template('add.html', site_name=SITE_NAME)

@app.route('/delete/<int:id_>', methods=['POST'])
def delete(id_):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("DELETE FROM projects WHERE id = %s;", (id_,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('index'))

@app.route('/change/<int:id_>', methods=['GET', 'POST'])
def change(id_):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    if request.method == 'POST':
        title = request.form['title']
        type_ = request.form['type']
        release_date = request.form['release_date']
        link_texts = request.form.getlist('link_text[]')
        link_urls = request.form.getlist('link_url[]')

        links = [
            {"text": str(t), "url": str(u)}
            for t, u in zip(link_texts, link_urls)
            if t.strip() and u.strip()
        ]

        # Format date
        dt = datetime.strptime(release_date, "%Y-%m-%d")
        formatted_date = dt.strftime("%d %B %Y")

        # Update project details
        cur.execute("""
            UPDATE projects
            SET title = %s, type = %s, release_date = %s, formatted_date = %s
            WHERE id = %s;
        """, (title, type_, release_date, formatted_date, id_))

        # Clear old links and insert new ones
        cur.execute("DELETE FROM project_links WHERE project_id = %s;", (id_,))
        for link in links:
            link = dict(link)  # Ensure plain dict
            cur.execute("""
                INSERT INTO project_links (project_id, link_text, link_url)
                VALUES (%s, %s, %s);
            """, (id_, link['text'], link['url']))

        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('index'))

    else:
        # Load current data
        cur.execute("SELECT id, title, type, release_date FROM projects WHERE id = %s;", (id_,))
        project = dict(cur.fetchone())  # Ensure it's a dict, not RealDictRow

        cur.execute("SELECT link_text, link_url FROM project_links WHERE project_id = %s;", (id_,))
        links = [dict(row) for row in cur.fetchall()]  # Convert rows to plain dicts

        cur.close()
        conn.close()
        return render_template('change.html', project=project, links=links, site_name=SITE_NAME, id=id_)

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

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("DELETE FROM rec_emails WHERE email = %s;", (email,))
    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for('manage_emails'))

if __name__ == '__main__':
    # Start Flask app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
