import sqlite3

# Connect to the database
conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# Create trains table
cursor.execute("""
CREATE TABLE IF NOT EXISTS trains (
    train_id INTEGER PRIMARY KEY AUTOINCREMENT,
    train_number TEXT UNIQUE,
    train_name TEXT,
    source TEXT,
    destination TEXT
)
""")

# Create coaches table
cursor.execute("""
CREATE TABLE IF NOT EXISTS coaches (
    coach_id INTEGER PRIMARY KEY AUTOINCREMENT,
    train_number TEXT,
    coach_number TEXT,
    coach_type TEXT,
    total_berths INTEGER,
    UNIQUE(train_number, coach_number)
)
""")

# Create berths table
cursor.execute("""
CREATE TABLE IF NOT EXISTS berths (
    berth_id INTEGER PRIMARY KEY AUTOINCREMENT,
    coach_id INTEGER,
    berth_number INTEGER,
    berth_type TEXT,
    status TEXT DEFAULT 'Available',
    FOREIGN KEY(coach_id) REFERENCES coaches(coach_id),
    UNIQUE(coach_id, berth_number)
)
""")

# Create passengers table
cursor.execute("""
CREATE TABLE IF NOT EXISTS passengers (
    passenger_id INTEGER PRIMARY KEY AUTOINCREMENT,
    passenger_name TEXT,
    train_number TEXT,
    coach_number TEXT,
    berth_number INTEGER,
    preferred_berth TEXT
)
""")

# Insert sample trains
trains = [
    ("12627", "Karnataka Express (Sample)",
     "Bengaluru", "New Delhi"),

    ("16589", "Rani Chennamma Express (Sample)",
     "Bengaluru", "Sangli"),

    ("12649", "Sampark Kranti Express (Sample)",
     "Bengaluru", "Hazrat Nizamuddin")
]

cursor.executemany("""
INSERT OR IGNORE INTO trains
(train_number, train_name, source, destination)
VALUES (?, ?, ?, ?)
""", trains)

# Insert sample coaches
coaches = [
    ("12627", "S1", "Sleeper", 72),
    ("12627", "S2", "Sleeper", 72),
    ("16589", "S1", "Sleeper", 72),
    ("16589", "S2", "Sleeper", 72),
    ("12649", "S1", "Sleeper", 72)
]

cursor.executemany("""
INSERT OR IGNORE INTO coaches
(train_number, coach_number, coach_type, total_berths)
VALUES (?, ?, ?, ?)
""", coaches)

# Generate berth details
berth_types = [
    "Lower", "Middle", "Upper",
    "Lower", "Middle", "Upper",
    "Side Lower", "Side Upper"
]

cursor.execute("SELECT coach_id FROM coaches")

for (coach_id,) in cursor.fetchall():
    for number in range(1, 73):

        berth_type = berth_types[(number - 1) % 8]

        cursor.execute("""
        INSERT OR IGNORE INTO berths
        (coach_id, berth_number, berth_type, status)
        VALUES (?, ?, ?, 'Available')
        """, (coach_id, number, berth_type))

# Insert sample passengers
cursor.execute("SELECT COUNT(*) FROM passengers")

if cursor.fetchone()[0] == 0:

    passengers = [
        ("Rahul", "12627", "S1", 1, "Side Lower"),
        ("Priya", "12627", "S1", 7, "Lower"),
        ("Arun", "12627", "S1", 2, "Upper"),
        ("Sneha", "12627", "S1", 3, "Middle"),
        ("Kiran", "16589", "S1", 10, "Lower"),
        ("Meena", "16589", "S1", 11, "Side Lower")
    ]

    cursor.executemany("""
    INSERT INTO passengers
    (passenger_name, train_number, coach_number,
     berth_number, preferred_berth)
    VALUES (?, ?, ?, ?, ?)
    """, passengers)

# Save changes
conn.commit()

# Update berth status for sample passengers
cursor.execute("""
    UPDATE berths
    SET status = 'Available'
""")

cursor.execute("""
    UPDATE berths
    SET status = 'Occupied'
    WHERE EXISTS (
        SELECT 1
        FROM passengers p
        JOIN coaches c
          ON c.train_number = p.train_number
         AND c.coach_number = p.coach_number
        WHERE c.coach_id = berths.coach_id
          AND p.berth_number = berths.berth_number
    )
""")
conn.close()

print("================================")
print("DATABASE CREATED SUCCESSFULLY!")
print("3 sample trains added.")
print("5 sample coaches added.")
print("360 sample berths generated.")
print("6 sample passengers added.")
print("================================")