

import sqlite3

import os

db_path = "chatbot.db"

print(f"Checking {os.path.abspath(db_path)}")

conn = sqlite3.connect(db_path)

cursor = conn.cursor()

info = cursor.execute("PRAGMA table_info(chat_sessions)").fetchall()

print("Columns in chat_sessions:")

for col in info:

    print(col)

conn.close()

