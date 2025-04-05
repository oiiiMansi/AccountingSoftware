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

# ✅ User Registration Route
@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]

        # Hash the password before storing
        hashed_password = generate_password_hash(password)

        conn = connect_db()
        cursor = conn.cursor()

        try:
            cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", 
                           (username, hashed_password, role))
            conn.commit()
            flash("User registered successfully! Please log in.", "success")
            return redirect(url_for("auth.login"))

        except mysql.connector.IntegrityError:
            flash("Username already exists!", "danger")

        finally:
            cursor.close()
            conn.close()

    return render_template("register.html")

# ✅ Login Route
@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        conn.close()

        if user:
            print(f"Stored Hash: {user['password']}")
            print(f"Entered Password: {password}")
            print(f"Check Result: {check_password_hash(user['password'], password)}")

        if user and check_password_hash(user["password"], password):
            login_user(User(user["id"], user["username"], user["role"]))

            # Get 'next' from form (POST) or fallback to home
            next_page = request.form.get("next") or url_for("home")
            return redirect(next_page)
        else:
            flash("Invalid credentials!", "danger")

    # For GET method
    next_page = request.args.get("next")
    return render_template("login.html", next=next_page)

# ✅ Logout Route
@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
