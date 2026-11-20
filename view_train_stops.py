
import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

query = """
SELECT
    t.train_number,
    s.station_name,
    s.arrival_time,
    s.departure_time
FROM trains t
JOIN train_stops s
    ON t.train_id = s.train_id
WHERE t.train_number = ?
ORDER BY s.stop_order
"""

cursor.execute(query, ("SS001",))

print("\nSMARTSEAT TRAIN SS001 TIMETABLE\n")

for row in cursor.fetchall():
    train_number, station, arrival, departure = row

    print(
        f"{station:15} | "
        f"Arrival: {arrival or '-':5} | "
        f"Departure: {departure or '-':5}"
    )

conn.close()
