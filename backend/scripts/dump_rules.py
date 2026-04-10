

import sqlite3

conn = sqlite3.connect('chatbot.db')

cursor = conn.cursor()

res = cursor.execute('SELECT b.name, r.weekday, r.start_time, r.end_time FROM business_availability_rules r JOIN businesses b ON r.business_id = b.id').fetchall()

for row in res:

    print(row)

conn.close()

