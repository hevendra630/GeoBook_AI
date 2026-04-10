

import sqlite3

conn = sqlite3.connect('chatbot.db')

cursor = conn.cursor()

RULES = [

    ('salon', ['salon', 'barber', 'hair', 'beauty', 'spa', 'parlour']),

    ('hospital', ['hospital', 'emergency', 'medical center']),

    ('clinic', ['clinic', 'doctor', 'physician']),

    ('dental', ['dental', 'dentist']),

    ('restaurant', ['restaurant', 'food', 'bakery', 'hotel', 'biryani', 'cafe']),

    ('school', ['school', 'college', 'university']),

]

print("Starting DB Clean...")

for category, keywords in RULES:

    for kw in keywords:

        cursor.execute(f"UPDATE businesses SET category = ? WHERE name LIKE ?", (category, f'%{kw}%'))

        if cursor.rowcount > 0:

            print(f"Updated {cursor.rowcount} businesses to '{category}' using keyword '{kw}'")

conn.commit()

conn.close()

print("DB Clean Complete!")

