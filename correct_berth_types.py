
import sqlite3
import os

db_path = os.path.join(
    os.path.dirname(__file__), "database.db"
)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

patterns = {
    "Sleeper": [
        "Lower Berth",
        "Middle Berth",
        "Upper Berth",
        "Side Lower (Window-side)",
        "Lower Berth",
        "Middle Berth",
        "Upper Berth",
        "Side Upper (Window-side)"
    ],
    "AC 3 Tier": [
        "Lower Berth",
        "Middle Berth",
        "Upper Berth",
        "Side Lower (Window-side)",
        "Lower Berth",
        "Middle Berth",
        "Upper Berth",
        "Side Upper (Window-side)"
    ],
    "AC 2 Tier": [
        "Lower Berth",
        "Upper Berth",
        "Side Lower (Window-side)",
        "Lower Berth",
        "Upper Berth",
        "Side Upper (Window-side)"
    ]
}

coaches = cursor.execute("""
    SELECT coach_id, coach_type
    FROM coaches
""").fetchall()

for coach_id, coach_type in coaches:

    if coach_type not in patterns:
        continue

    pattern = patterns[coach_type]

    seats = cursor.execute("""
        SELECT berth_id, berth_number
        FROM berths
        WHERE coach_id = ?
    """, (coach_id,)).fetchall()

    for berth_id, berth_number in seats:
        position = (int(berth_number) - 1) % len(pattern)

        cursor.execute("""
            UPDATE berths
            SET berth_type = ?
            WHERE berth_id = ?
        """, (pattern[position], berth_id))

conn.commit()
conn.close()

print("SUCCESS: Berth positions corrected!")
