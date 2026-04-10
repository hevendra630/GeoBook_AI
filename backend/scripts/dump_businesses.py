

import sqlite3

conn = sqlite3.connect('chatbot.db')

cursor = conn.cursor()

res = cursor.execute('SELECT name, category FROM businesses').fetchall()

for row in res:

    print(f"Name: {row[0]} | Category: {row[1]}")

conn.close()

