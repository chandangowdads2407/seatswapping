import sqlite3

# Connect to the database
conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# Display train details
print("\n========== TRAIN DETAILS ==========")

cursor.execute("SELECT * FROM trains")

for train in cursor.fetchall():
    print(train)

# Display coach details
print("\n========== COACH DETAILS ==========")

cursor.execute("SELECT * FROM coaches")

for coach in cursor.fetchall():
    print(coach)

# Display the first 15 berths of train 12627, coach S1
print("\n========== BERTH DETAILS ==========")

cursor.execute("""
SELECT
    t.train_number,
    c.coach_number,
    b.berth_number,
    b.berth_type,
    b.status
FROM berths b
JOIN coaches c ON b.coach_id = c.coach_id
JOIN trains t ON c.train_number = t.train_number
WHERE t.train_number = '12627'
AND c.coach_number = 'S1'
ORDER BY b.berth_number
LIMIT 15
""")

for berth in cursor.fetchall():
    print(berth)

# Close the database connection
conn.close()
