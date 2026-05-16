import sqlite3
import os

db_path = 'notes.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE notes ADD COLUMN is_locked BOOLEAN DEFAULT 0")
        cursor.execute("ALTER TABLE notes ADD COLUMN hashed_lock_password VARCHAR")
        conn.commit()
        print("Columns added successfully")
    except sqlite3.OperationalError as e:
        print(f"Error: {e}")
    conn.close()
else:
    print("Database not found")
