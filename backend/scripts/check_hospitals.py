

import sqlite3

conn = sqlite3.connect('chatbot.db')

cursor = conn.cursor()

res = cursor.execute("SELECT name, category FROM businesses WHERE name LIKE '%Hospital%'").fetchall()

print(res)

conn.close()

