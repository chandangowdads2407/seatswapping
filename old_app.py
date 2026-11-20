from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3

app = Flask(__name__)
app.secret_key = "smartseat-prototype-key"


# Connect to the database
def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


# Homepage
@app.route("/")
def home():
    conn = get_db_connection()

    trains = conn.execute(
        "SELECT * FROM trains"
    ).fetchall()

    conn.close()

    return render_template("index.html", trains=trains)


# Display coaches
@app.route("/coaches/<train_number>")
def coaches(train_number):
    conn = get_db_connection()

    train = conn.execute(
        "SELECT * FROM trains WHERE train_number = ?",
        (train_number,)
    ).fetchone()

    if train is None:
        conn.close()
        return "Train not found", 404

    coach_list = conn.execute(
        """
        SELECT * FROM coaches
        WHERE train_number = ?
        ORDER BY coach_number
        """,
        (train_number,)
    ).fetchall()

    conn.close()

    return render_template(
        "coaches.html",
        train=train,
        coaches=coach_list
    )


# Display berths
@app.route("/berths/<int:coach_id>")
def berths(coach_id):
    conn = get_db_connection()

    coach = conn.execute(
        "SELECT * FROM coaches WHERE coach_id = ?",
        (coach_id,)
    ).fetchone()

    if coach is None:
        conn.close()
        return "Coach not found", 404

    berth_list = conn.execute(
        "SELECT * FROM berths WHERE coach_id = ? ORDER BY berth_number",
        (coach_id,)
    ).fetchall()

    conn.close()

    return render_template(
        "berths.html",
        coach=coach,
        berths=berth_list
    )


# Test route
@app.route("/test")
def test():
    return "Flask routes are working!"


# Seat swapping
@app.route("/swap", methods=["GET", "POST"])
def swap():
    conn = get_db_connection()

    if request.method == "POST":

        passenger1_id = request.form.get("passenger1", type=int)
        passenger2_id = request.form.get("passenger2", type=int)

        if not passenger1_id or not passenger2_id:
            conn.close()
            flash("Please select both passengers.", "error")
            return redirect(url_for("swap"))

        if passenger1_id == passenger2_id:
            conn.close()
            flash("Please select two different passengers.", "error")
            return redirect(url_for("swap"))

        try:
            conn.execute("BEGIN IMMEDIATE")

            p1 = conn.execute(
                "SELECT * FROM passengers WHERE passenger_id = ?",
                (passenger1_id,)
            ).fetchone()

            p2 = conn.execute(
                "SELECT * FROM passengers WHERE passenger_id = ?",
                (passenger2_id,)
            ).fetchone()

            if p1 is None or p2 is None:
                conn.rollback()
                flash("Passenger not found.", "error")

            elif p1["train_number"] != p2["train_number"]:
                conn.rollback()
                flash(
                    "Both passengers must be on the same train.",
                    "error"
                )

            elif p1["coach_number"] != p2["coach_number"]:
                conn.rollback()
                flash(
                    "Both passengers must be in the same coach.",
                    "error"
                )

            else:
                berth1 = conn.execute(
                    """
                    SELECT b.status
                    FROM berths b
                    JOIN coaches c ON c.coach_id = b.coach_id
                    WHERE c.train_number = ?
                      AND c.coach_number = ?
                      AND b.berth_number = ?
                    """,
                    (
                        p1["train_number"],
                        p1["coach_number"],
                        p1["berth_number"]
                    )
                ).fetchone()

                berth2 = conn.execute(
                    """
                    SELECT b.status
                    FROM berths b
                    JOIN coaches c ON c.coach_id = b.coach_id
                    WHERE c.train_number = ?
                      AND c.coach_number = ?
                      AND b.berth_number = ?
                    """,
                    (
                        p2["train_number"],
                        p2["coach_number"],
                        p2["berth_number"]
                    )
                ).fetchone()

                if berth1 is None or berth2 is None:
                    conn.rollback()
                    flash(
                        "One or both berth assignments are invalid.",
                        "error"
                    )

                elif (
                    berth1["status"] != "Occupied"
                    or berth2["status"] != "Occupied"
                ):
                    conn.rollback()
                    flash(
                        "Both berths must be occupied for a swap.",
                        "error"
                    )

                else:
                    old_berth1 = p1["berth_number"]
                    old_berth2 = p2["berth_number"]

                    conn.execute(
                        """
                        UPDATE passengers
                        SET berth_number = ?
                        WHERE passenger_id = ?
                        """,
                        (old_berth2, passenger1_id)
                    )

                    conn.execute(
                        """
                        UPDATE passengers
                        SET berth_number = ?
                        WHERE passenger_id = ?
                        """,
                        (old_berth1, passenger2_id)
                    )

                    conn.commit()

                    flash(
                        f"Swap successful! {p1['passenger_name']} "
                        f"moved to berth {old_berth2}, and "
                        f"{p2['passenger_name']} moved to berth "
                        f"{old_berth1}.",
                        "success"
                    )

        except sqlite3.Error:
            conn.rollback()

            flash(
                "A database error occurred. No swap was completed.",
                "error"
            )

        finally:
            conn.close()

        return redirect(url_for("swap"))

    passengers = conn.execute(
        """
        SELECT * FROM passengers
        ORDER BY passenger_id
        """
    ).fetchall()

    conn.close()

    return render_template(
        "swap.html",
        passengers=passengers
    )


# Start the Flask application
if __name__ == "__main__":
    app.run(debug=True)