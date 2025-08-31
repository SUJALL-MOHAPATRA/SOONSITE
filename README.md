SOONSITE – Project Release Reminder

SOONSITE is a Flask-based web application that helps store and manage upcoming movies' or tv shows' releases while automatically notifying some recipients when release dates are near. It is fully backed by PostgreSQL and now includes a working email notification system.

Features
Project Management

Add new releases with title, type, and release date.

Edit or delete existing releases.

Attach multiple external links (trailers, news, etc.) to each release.

Email Management

Add recipient emails.

Delete recipient emails.

All emails are stored in the PostgreSQL database (no JSON files).

Automated Email Reminders (via emailer.py)

emailer.py is fully set up and integrated.

Sends notifications if a release date is 10 days away or less.

Prevents duplicate notifications by marking projects as notified.

Database-backed

Fully migrated from JSON to PostgreSQL.

Proper foreign key relationships with cascading deletes ensure data consistency.

Session Authentication

Simple login/logout system to protect admin features.

Tech Stack

Backend

Flask (Python web framework)

psycopg2 (PostgreSQL adapter)

smtplib (for sending emails via Gmail SMTP)

Database

PostgreSQL with these tables:

projects – stores release data.

project_links – stores related links.

rec_emails – stores recipient email addresses.

Frontend

HTML5, CSS3

FontAwesome icons for buttons

Database Schema
projects
Column	Type	Description
id (PK)	SERIAL	Primary key
title	TEXT	Project/movie/show title
type	TEXT	Type (Movie, TV Show, etc.)
release_date	DATE	Original release date
notified	BOOLEAN	Whether email reminder was sent
project_links
Column	Type	Description
link_id (PK)	SERIAL	Primary key
project_id (FK)	INT	References projects.id (ON DELETE CASCADE)
text	TEXT	Link label (e.g., “Trailer”)
url	TEXT	Link URL
rec_emails
Column	Type	Description
id (PK)	SERIAL	Primary key
email	TEXT	Recipient email (unique, required)
Project Structure
SOONSITE/
│
├── app.py               # Flask app entry point  
├── emailer.py           # Automated email reminder script (fully set up!)  
├── templates/  
│   ├── index.html       # Homepage (list releases)  
│   ├── change.html      # Edit release page  
│   ├── emails.html      # Manage email recipients  
│   └── login.html       # Simple login form  
├── static/  
│   └── style.css        # Website styling  
├── requirements.txt     # Python dependencies  
└── README.md            # Project documentation  

Application Flow

Homepage (/)

Fetches all upcoming projects and links from PostgreSQL.

Displays them in a scrollable list with Edit/Delete buttons.

External links (trailers/news) appear in a dropdown menu.

Admin controls:

Edit → /change/<project_id>

Delete → /delete/<project_id>

Add Release (/add)

Form to enter title, type, release date, and optional links.

Inserts data into projects and project_links tables.

Redirects to homepage after save.

Edit Release (/change/<project_id>)

Pre-populates form with project data and links.

Allows inline adding/removing/changing links.

Updates database upon save.

Delete Release (/delete/<project_id>)

Deletes project from projects table.

Cascades automatically to remove related links.

Manage Emails (/emails)

Lists all recipient emails from rec_emails.

Add new emails via comma-separated input.

Delete individual emails via button.

Changes update instantly in DB.

Email Reminder System (emailer.py)
What it does:

Runs as python emailer.py.

Checks for projects with release dates ≤ 10 days.

Sends notification emails to all recipients using Gmail SMTP.

Marks projects as notified to prevent duplicate alerts.

SMTP Setup

Uses Gmail App Password (stored securely in SENDER_PASSWORD).

Sends via SSL on port 465.

All recipients are placed in BCC for privacy.

Important Implementation Details

Cursor Type: Uses RealDictCursor to access DB columns by name.

Session Auth: Simple session check (session['logged_in']).

Cascade Deletes: No orphaned records due to proper foreign keys.

Template Safety: Fixes applied to prevent Jinja undefined errors.

Deployment Guide

Local Run

pip install -r requirements.txt
python app.py


Visit http://127.0.0.1:5000/

Database Setup

CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    type TEXT NOT NULL,
    release_date DATE NOT NULL,
    notified BOOLEAN DEFAULT FALSE
);

CREATE TABLE project_links (
    link_id SERIAL PRIMARY KEY,
    project_id INT REFERENCES projects(id) ON DELETE CASCADE,
    text TEXT,
    url TEXT
);

CREATE TABLE rec_emails (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL
);

Email Workflow

To automate emailer.py without running it manually, you can:

Use GitHub Actions to trigger it once daily.

Use Render Cron Jobs (paid option).

Integrate into Flask routes to run on visits (less reliable).
