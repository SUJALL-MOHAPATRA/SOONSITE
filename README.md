🎬 SOONSITE – Project Release Reminder

SOONSITE is a Flask-based web application to track and manage upcoming Movies or TV shows and automatically notify recipients as release dates approach.
It is fully powered by PostgreSQL and now includes a working email notification system via emailer.py.

✨ Features

    📌 Project Management
        ➕ Add new releases with title, type, and release date
        ✏️ Edit or ❌ delete existing releases
        🔗 Attach multiple external links (trailers, news, etc.)
    
    📧 Email Management
        ➕ Add recipient emails
        ❌ Delete recipient emails
        💾 All emails are stored in PostgreSQL (no JSON files!)
    
    🕒 Automated Email Reminders (emailer.py)
        ✅ Fully set up and integrated
        ⏳ Sends notifications 10 days before release date
        🔒 Prevents duplicate alerts by marking projects as notified
    
    🗄 Database-backed
        📤 Migrated entirely from JSON to PostgreSQL
        🔗 Foreign key relationships with cascade deletes for data consistency
    
    🔑 Session Authentication
        Simple login/logout system to protect admin features

🛠 Tech Stack

    Backend
        🐍 Flask (Python web framework)
        🗃 psycopg2 (PostgreSQL adapter)
        📬 smtplib (Gmail SMTP for email)
    
    Database
        🐘 PostgreSQL with tables:
                projects – stores release data
                project_links – stores related links
                rec_emails – stores recipient email addresses
    
    Frontend
        🌐 HTML5, CSS3
        🎨 FontAwesome icons for buttons

🗂 Database Schema

    projects
        Column	        Type	    Description
        id (PK)	        SERIAL	    Primary key
        title	        TEXT	    Project/movie/show title
        type	        TEXT	    Type (Movie, TV Show, etc.)
        release_date	DATE	    Original release date
        notified	    BOOLEAN	    Whether email reminder was sent

    project_links
        Column	          Type	    Description
        link_id (PK)	  SERIAL	Primary key
        project_id (FK)	  INT	    References projects.id (ON DELETE CASCADE)
        text	          TEXT	    Link label (e.g., “Trailer”)
        url	              TEXT	    Link URL

    rec_emails
        Column	Type	Description
        id (PK)	SERIAL	Primary key
        email	TEXT	Recipient email (unique, required)

📁 Project Structure

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

🔄 Application Flow

    🏠 Homepage (/)
            Fetches projects + links from PostgreSQL
            Displays them with Edit/Delete buttons
            Dropdown for external links (trailers/news)
        
    ➕ Add Release (/add)
            Form for title, type, release date, and links
            Inserts into DB and redirects to homepage

    ✏️ Edit Release (/change/<project_id>)
            Pre-fills form with project data + links
            Inline link management + DB update
    
    ❌ Delete Release (/delete/<project_id>)
            Deletes project and cascades link deletion
    
    📧 Manage Emails (/emails)
            Lists all emails from rec_emails
            Add via comma-separated input
            Delete instantly with a button

📬 Email Reminder System (emailer.py)

    How it works:
        Run using python emailer.py
        Finds releases ≤ 10 days away
        Sends emails via Gmail SMTP to all recipients
        Marks projects as notified
    
    SMTP Setup:
        Uses Gmail App Password (SENDER_PASSWORD)
        SSL on port 465
        Recipients added in BCC for privacy

🔧 Important Implementation Details

    Cursor Type: Uses RealDictCursor for column access by name
    Session Auth: Simple session['logged_in'] check
    Cascade Deletes: No orphan records in DB
    Template Safety: Fixed Jinja undefined errors

🚀 Deployment Guide
    
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

⏱ Email Workflow

To run emailer.py automatically:

    ⚙️ Use GitHub Actions (trigger daily)
    ⏰ Use Render Cron Jobs (paid option)
    🔗 Integrate into Flask routes to run during visits (less reliable)
