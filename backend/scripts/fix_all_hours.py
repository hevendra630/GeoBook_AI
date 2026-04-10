

import sqlite3

import uuid

conn = sqlite3.connect('chatbot.db')

cursor = conn.cursor()

businesses = cursor.execute('SELECT id, name FROM businesses').fetchall()

print(f"Found {len(businesses)} businesses")

for b_id, name in businesses:

    print(f"Adding 7-day rules for {name} ({b_id})")

    for day in range(7):

        

        try:

            cursor.execute('''
                INSERT OR REPLACE INTO business_availability_rules (id, business_id, weekday, start_time, end_time, slot_minutes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (str(uuid.uuid4()), b_id, day, '00:00:00', '23:59:00', 30))

        except Exception as e:

            print(f"  Error on day {day}: {e}")

conn.commit()

conn.close()

print("Done!")

