from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from models import User  # Import User class from models

auth = Blueprint("auth", __name__)

# Database Connection
def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="roxanne",
        database="accounting"
    )

# ✅ Register Route
@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]

        # Basic form validation
        if not username or not password or not role:
            flash("All fields are required!", "danger")
            return redirect(url_for("auth.register"))

        hashed_password = generate_password_hash(password)

        conn = connect_db()
        cursor = conn.cursor()

        try:
            # Check if username already exists
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            existing_user = cursor.fetchone()
            if existing_user:
                flash("Username already exists!", "danger")
                return redirect(url_for("auth.register"))

            # Insert the new user into the database
            cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                           (username, hashed_password, role))
            conn.commit()
            flash("User registered successfully! Please log in.", "success")
            return redirect(url_for("auth.login"))

        except mysql.connector.Error as err:
            flash(f"Error: {err}", "danger")
        finally:
            cursor.close()
            conn.close()

    return render_template("register.html")


# ✅ Login Route
@auth.route("/login", methods=["GET", "POST"])
def login():
    # For GET, capture ?next from URL
    next_page = request.args.get("next")

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Basic form validation
        if not username or not password:
            flash("Please enter both username and password.", "danger")
            return redirect(url_for("auth.login"))

        conn = connect_db()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            if user and check_password_hash(user["password"], password):
                login_user(User(user["id"], user["username"], user["role"]))
                # Redirect to the next page or home if not specified
                next_page = request.form.get("next") or next_page or url_for("home")
                return redirect(next_page)
            else:
                flash("Invalid credentials! Please check your username and password.", "danger")

        except mysql.connector.Error as err:
            flash(f"Error: {err}", "danger")
        finally:
            cursor.close()
            conn.close()

    return render_template("login.html", next=next_page)


# ✅ Logout Route
@auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have successfully logged out.", "success")
    return redirect(url_for("auth.login"))
