from datetime import date
from flask import (
    Flask, render_template, request,
    redirect, url_for, flash, session
)
import sqlite3
import os
import re
import secrets
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "smartseat-college-project-secret-key"

DATABASE = os.path.join(app.root_path, "database.db")


# Connect to database
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# Create passenger users table without deleting existing tables

# Create passenger users table without deleting existing tables
def create_user_table():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            passenger_name TEXT NOT NULL,
            phone_number TEXT UNIQUE NOT NULL,
            password_hash TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Add username to existing databases without deleting data
    columns = [
        row["name"]
        for row in conn.execute("PRAGMA table_info(users)").fetchall()
    ]

    if "username" not in columns:
        conn.execute("ALTER TABLE users ADD COLUMN username TEXT")

    conn.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username
        ON users(username)
        WHERE username IS NOT NULL AND username != ''
    """)

    conn.commit()
    conn.close()


# Create the table
create_user_table()


# Home page
@app.route("/")
def home():
    return render_template("index.html")

# Passenger login - existing registered users
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    if not username or not password:
        flash("Enter your username and password.", "error")
        return redirect(url_for("login"))

    conn = get_db_connection()

    user = conn.execute("""
        SELECT *
        FROM users
        WHERE username = ?
    """, (username,)).fetchone()

    conn.close()

    if user is None or not user["password_hash"]:
        flash("Invalid username or password.", "error")
        return redirect(url_for("login"))

    if not check_password_hash(user["password_hash"], password):
        flash("Invalid username or password.", "error")
        return redirect(url_for("login"))

    session.clear()
    session["user_id"] = user["user_id"]
    session["passenger_name"] = user["passenger_name"]
    session["phone_number"] = user["phone_number"]

    flash("Login successful!", "success")
    return redirect(url_for("dashboard"))


# New passenger registration
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "GET":
        return render_template("register.html")

    name = request.form.get("passenger_name", "").strip()
    username = request.form.get("username", "").strip()
    phone = request.form.get("phone_number", "").strip()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not name or not username or not phone:
        flash("Please fill in all required fields.", "error")
        return redirect(url_for("register"))

    if not re.fullmatch(r"[A-Za-z0-9_]{4,20}", username):
        flash("Username must be 4-20 characters using letters, numbers or underscores.", "error")
        return redirect(url_for("register"))

    if not re.fullmatch(r"[0-9]{10}", phone):
        flash("Enter a valid 10-digit phone number.", "error")
        return redirect(url_for("register"))

    if len(password) < 8:
        flash("Password must contain at least 8 characters.", "error")
        return redirect(url_for("register"))

    if password != confirm_password:
        flash("Password and confirm password do not match.", "error")
        return redirect(url_for("register"))

    conn = get_db_connection()

    existing_username = conn.execute(
        "SELECT user_id FROM users WHERE username = ?",
        (username,)
    ).fetchone()

    existing_phone = conn.execute(
        "SELECT * FROM users WHERE phone_number = ?",
        (phone,)
    ).fetchone()

    conn.close()

    if existing_username:
        flash("This username is already registered. Choose another.", "error")
        return redirect(url_for("register"))

    # Allow an old prototype account without a username to be upgraded.
    if existing_phone and existing_phone["username"]:
        flash("This phone number is already registered. Please log in.", "error")
        return redirect(url_for("register"))

    otp = str(secrets.randbelow(900000) + 100000)

    session.clear()
    session["pending_registration"] = {
        "passenger_name": name,
        "username": username,
        "phone_number": phone,
        "password_hash": generate_password_hash(password)
    }
    session["registration_otp"] = otp

    return render_template(
        "verify_registration.html",
        demo_otp=otp
    )


# Verify OTP and complete registration
@app.route("/verify-registration", methods=["POST"])
def verify_registration():

    entered_otp = request.form.get("otp", "").strip()
    saved_otp = session.get("registration_otp")
    pending = session.get("pending_registration")

    if not saved_otp or not pending:
        flash("Registration session expired. Please register again.", "error")
        return redirect(url_for("register"))

    if not re.fullmatch(r"[0-9]{6}", entered_otp) or entered_otp != saved_otp:
        flash("Incorrect OTP. Please try again.", "error")
        return render_template(
            "verify_registration.html",
            demo_otp=saved_otp
    )

    conn = get_db_connection()

    # Check again in case the username was registered during verification.
    existing_username = conn.execute(
        "SELECT user_id FROM users WHERE username = ?",
        (pending["username"],)
    ).fetchone()

    if existing_username:
        conn.close()
        session.clear()
        flash("This username is already registered. Please choose another.", "error")
        return redirect(url_for("register"))

    existing_phone = conn.execute(
        "SELECT * FROM users WHERE phone_number = ?",
        (pending["phone_number"],)
    ).fetchone()

    if existing_phone:
        # Upgrade an old prototype account that has no username.
        if existing_phone["username"]:
            conn.close()
            session.clear()
            flash("This phone number is already registered. Please log in.", "error")
            return redirect(url_for("login"))

        conn.execute("""
            UPDATE users
            SET passenger_name = ?,
                username = ?,
                password_hash = ?
            WHERE user_id = ?
        """, (
            pending["passenger_name"],
            pending["username"],
            pending["password_hash"],
            existing_phone["user_id"]
        ))

        user_id = existing_phone["user_id"]

    else:
        cursor = conn.execute("""
            INSERT INTO users
                (passenger_name, username, phone_number, password_hash)
            VALUES (?, ?, ?, ?)
        """, (
            pending["passenger_name"],
            pending["username"],
            pending["phone_number"],
            pending["password_hash"]
        ))

        user_id = cursor.lastrowid

    conn.commit()
    conn.close()

    session.clear()
    session["user_id"] = user_id
    session["passenger_name"] = pending["passenger_name"]
    session["phone_number"] = pending["phone_number"]

    flash("Registration completed successfully!", "success")
    return redirect(url_for("dashboard"))

# Search trains between selected stations

# View coaches for a selected train
@app.route("/coaches/<int:train_id>")
def view_coaches(train_id):

    if "user_id" not in session:
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    conn = get_db_connection()

    train = conn.execute("""
        SELECT train_id, train_number, train_name
        FROM trains
        WHERE train_id = ?
    """, (train_id,)).fetchone()

    if train is None:
        conn.close()
        flash("Train not found.", "error")
        return redirect(url_for("search_trains"))

    coaches = conn.execute("""
        SELECT coach_id, coach_number, coach_type, total_berths
FROM coaches
WHERE train_number = ?
ORDER BY CASE coach_number
    WHEN 'S1' THEN 1
    WHEN 'GS1' THEN 2
    WHEN 'B1' THEN 3
    WHEN 'A1' THEN 4
    ELSE 5
END
    """, (train["train_number"],)).fetchall()

    conn.close()

    return render_template(
        "select_coaches.html",
        train=train,
        coaches=coaches
    )

# View berths for a selected coach
@app.route("/berths/<int:coach_id>")
def view_berths(coach_id):

    if "user_id" not in session:
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    conn = get_db_connection()

    coach = conn.execute("""
        SELECT
            c.coach_id,
            c.train_number,
            c.coach_number,
            c.coach_type,
            c.total_berths,
            t.train_id
        FROM coaches c
JOIN trains t ON t.train_number = c.train_number
        WHERE c.coach_id = ?
    """, (coach_id,)).fetchone()

    if coach is None:
        conn.close()
        flash("Coach not found.", "error")
        return redirect(url_for("search_trains"))

    berths = conn.execute("""
        SELECT berth_id, berth_number, berth_type, status
        FROM berths
        WHERE coach_id = ?
        ORDER BY berth_number
    """, (coach_id,)).fetchall()

    conn.close()

    return render_template(
        "berths.html",
        coach=coach,
        berths=berths
    )

# Passenger dashboard
@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        passenger_name=session.get("passenger_name"),
        phone_number=session.get("phone_number")
    )


# TT portal
@app.route("/tt-dashboard")
def tt_dashboard():
    return render_template("tt_dashboard.html")


# Logout
@app.route("/logout")
def logout():

    session.clear()

    flash("You have logged out successfully.", "success")

    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)