import sqlite3
import os

# Check whether the database exists
print("Database exists:", os.path.exists("database.db"))

# Connect to the database
conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# Display all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")

tables = cursor.fetchall()

print("\nTables found in database:")
for table in tables:
    print(table[0])

# Check whether the trains table exists
if ("trains",) in tables:
    print("\nSUCCESS: Trains table exists!")

    cursor.execute("SELECT * FROM trains")

    print("\nTrain details:")
    for train in cursor.fetchall():
        print(train)
else:
    print("\nERROR: Trains table is missing.")
    print("Please run create_database.py first.")

conn.close()
