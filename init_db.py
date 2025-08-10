import sqlite3
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB = os.path.join(BASE_DIR, 'dlmtc_lcs.db')  # Make sure this matches the DB name in your app

conn = sqlite3.connect(DB)
cursor = conn.cursor()

# Create 'session' table
cursor.execute('''
CREATE TABLE IF NOT EXISTS session (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    project TEXT,
    frequency TEXT,
    month TEXT,
    location TEXT,
    attended_by TEXT,
    verified_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# Create 'checklist_item' table
cursor.execute('''
CREATE TABLE IF NOT EXISTS checklist_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER,
    item_no TEXT,
    panel_ref TEXT,
    asset_code TEXT,
    item_description TEXT,
    values_observation TEXT,
    any_abnormality TEXT,
    remarks TEXT,
    FOREIGN KEY(session_id) REFERENCES session(id) ON DELETE CASCADE
)
''')

conn.commit()
conn.close()

print("✅ Database and tables created successfully.")
