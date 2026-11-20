
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")

# Four coach types for every train
coach_details = [
    ("S1", "Sleeper", 72),
    ("GS1", "General", 90),
    ("B1", "AC 3 Tier", 72),
    ("A1", "AC 2 Tier", 48)
]

def get_berth_type(coach_type, number):
    if coach_type == "General":
        return "Seat"

    if coach_type == "Sleeper":
        types = [
            "Lower", "Middle", "Upper",
            "Side Lower", "Side Upper", "Lower"
        ]
        return types[(number - 1) % len(types)]

    if coach_type == "AC 3 Tier":
        types = ["Lower", "Middle", "Upper",
                 "Side Lower", "Side Upper"]
        return types[(number - 1) % len(types)]

    if coach_type == "AC 2 Tier":
        types = ["Lower", "Upper",
                 "Side Lower", "Side Upper"]
        return types[(number - 1) % len(types)]

    return "Seat"


conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Get all trains
trains = cursor.execute(
    "SELECT train_number FROM trains"
).fetchall()

# Re-create sample coaches only for these trains.
# Delete their old berths first to avoid duplicate data.
for (train_number,) in trains:

    old_coaches = cursor.execute(
        "SELECT coach_id FROM coaches WHERE train_number = ?",
        (train_number,)
    ).fetchall()

    for (coach_id,) in old_coaches:
        cursor.execute(
            "DELETE FROM berths WHERE coach_id = ?",
            (coach_id,)
        )

    cursor.execute(
        "DELETE FROM coaches WHERE train_number = ?",
        (train_number,)
    )

    # Create four coaches
    for coach_number, coach_type, total in coach_details:

        cursor.execute("""
            INSERT INTO coaches
            (train_number, coach_number, coach_type, total_berths)
            VALUES (?, ?, ?, ?)
        """, (train_number, coach_number, coach_type, total))

        coach_id = cursor.lastrowid

        # Create seats/berths
        for number in range(1, total + 1):

            berth_type = get_berth_type(
                coach_type, number
            )

            cursor.execute("""
                INSERT INTO berths
                (coach_id, berth_number, berth_type, status)
                VALUES (?, ?, ?, ?)
            """, (
                coach_id,
                number,
                berth_type,
                "Available"
            ))

conn.commit()

print("SUCCESS: Four coach types created for every train!")

for train_number, coach_number, coach_type, total in cursor.execute("""
    SELECT train_number, coach_number, coach_type, total_berths
    FROM coaches
    ORDER BY train_number, coach_id
""").fetchall():
    print(train_number, coach_number, coach_type, total)

conn.close()
