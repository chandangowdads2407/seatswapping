
import sqlite3
from datetime import datetime, timedelta
import os

# Connect to the existing database
DATABASE = os.path.join(os.path.dirname(__file__), "database.db")
conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()

# Nine stations in the Mysuru-Bengaluru route
stations = [
    "Mysuru",
    "Pandavapura",
    "Mandya",
    "Maddur",
    "Channapatna",
    "Ramanagara",
    "Bidadi",
    "Kengeri",
    "Bengaluru"
]

# Minutes after departure from Mysuru
arrival_minutes = [None, 35, 57, 84, 106, 128, 145, 162, 184]

# Minutes after departure from Mysuru
departure_minutes = [0, 37, 59, 86, 108, 130, 147, 164, None]

# Create a separate table for station-wise train timings
cursor.execute("""
    CREATE TABLE IF NOT EXISTS train_stops (
        stop_id INTEGER PRIMARY KEY AUTOINCREMENT,
        train_id INTEGER NOT NULL,
        stop_order INTEGER NOT NULL,
        station_name TEXT NOT NULL,
        arrival_time TEXT,
        departure_time TEXT,
        FOREIGN KEY (train_id) REFERENCES trains(train_id)
    )
""")

# Create 10 demonstration trains
for i in range(10):

    train_number = f"SS{i + 1:03d}"
    train_name = f"SmartSeat Demo Express {i + 1:02d}"

    # Each train departs one hour after the previous train
    start_time = datetime.strptime("05:00", "%H:%M") + timedelta(hours=i)

    # Insert the train if it does not already exist
    cursor.execute(
        "SELECT train_id FROM trains WHERE train_number = ?",
        (train_number,)
    )
    existing_train = cursor.fetchone()

    if existing_train:
        train_id = existing_train[0]

        cursor.execute("""
            UPDATE trains
            SET train_name = ?, source = ?, destination = ?
            WHERE train_id = ?
        """, (train_name, "Mysuru", "Bengaluru", train_id))

    else:
        cursor.execute("""
            INSERT INTO trains
            (train_number, train_name, source, destination)
            VALUES (?, ?, ?, ?)
        """, (train_number, train_name, "Mysuru", "Bengaluru"))

        train_id = cursor.lastrowid

    # Refresh station timings for this sample train
    cursor.execute(
        "DELETE FROM train_stops WHERE train_id = ?",
        (train_id,)
    )

    for index, station in enumerate(stations):

        arrival = None
        departure = None

        if arrival_minutes[index] is not None:
            arrival = (
                start_time + timedelta(
                    minutes=arrival_minutes[index]
                )
            ).strftime("%H:%M")

        if departure_minutes[index] is not None:
            departure = (
                start_time + timedelta(
                    minutes=departure_minutes[index]
                )
            ).strftime("%H:%M")

        cursor.execute("""
            INSERT INTO train_stops
            (train_id, stop_order, station_name,
             arrival_time, departure_time)
            VALUES (?, ?, ?, ?, ?)
        """, (
            train_id,
            index + 1,
            station,
            arrival,
            departure
        ))

conn.commit()

# Display the inserted trains
print("\nSUCCESS: Sample train data added!")

cursor.execute("""
    SELECT train_number, train_name, source, destination
    FROM trains
    WHERE train_number LIKE 'SS%'
    ORDER BY train_number
""")

print("\nSMARTSEAT SAMPLE TRAINS:")
for train in cursor.fetchall():
    print(train)

print("\nStation timings have been added for all 10 trains.")

conn.close()
