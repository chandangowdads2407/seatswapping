
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Get every coach and its seats
coaches = cursor.execute("""
    SELECT coach_id, coach_type
    FROM coaches
""").fetchall()

for coach_id, coach_type in coaches:

    seats = cursor.execute("""
        SELECT berth_id, berth_number
        FROM berths
        WHERE coach_id = ?
        ORDER BY berth_number
    """, (coach_id,)).fetchall()

    for berth_id, berth_number in seats:
        number = int(berth_number)

        if coach_type == "General":
            # Six seats per row: two window, two middle, two aisle
            positions = [
                "Window Seat",
                "Middle Seat",
                "Aisle Seat",
                "Aisle Seat",
                "Middle Seat",
                "Window Seat"
            ]
            seat_type = positions[(number - 1) % 6]

        elif coach_type in ("Sleeper", "AC 3 Tier"):
            positions = [
                "Lower Berth",
                "Middle Berth",
                "Upper Berth",
                "Lower Berth",
                "Middle Berth",
                "Upper Berth",
                "Side Lower (Window-side)",
                "Side Upper (Window-side)"
            ]
            seat_type = positions[(number - 1) % 8]

        elif coach_type == "AC 2 Tier":
            positions = [
                "Lower Berth",
                "Upper Berth",
                "Lower Berth",
                "Upper Berth",
                "Side Lower (Window-side)",
                "Side Upper (Window-side)"
            ]
            seat_type = positions[(number - 1) % 6]

        else:
            seat_type = "Seat"

        cursor.execute("""
            UPDATE berths
            SET berth_type = ?
            WHERE berth_id = ?
        """, (seat_type, berth_id))

conn.commit()
conn.close()

print("SUCCESS: Seat types updated!")
print("Existing seat availability statuses are preserved.")
