import sqlite3
import os

db_path = 'notes.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(notes)")
    columns = cursor.fetchall()
    for col in columns:
        print(col)
    conn.close()
else:
    print("Database not found")
