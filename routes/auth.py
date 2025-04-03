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

# ✅ User Registration Route (New)
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

    return render_template("register.html")  # Ensure you have a register.html template

# ✅ Login Route (Already Exists, No Change Needed)
@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Connect to database and fetch user
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        conn.close()

        # Debugging: Check stored password
        if user:
            print(f"Stored Hash: {user['password']}")  
            print(f"Entered Password: {password}")  
            print(f"Check Result: {check_password_hash(user['password'], password)}")

        # Check if user exists and password is correct
        if user and check_password_hash(user["password"], password):
            login_user(User(user["id"], user["username"], user["role"]))
            return redirect(url_for("home"))  # Redirect to home page
        else:
            flash("Invalid credentials!", "danger")  # Show error message

    return render_template("login.html")  # Show login form if GET request

# ✅ Logout Route
@auth.route("/logout")
@login_required  # Ensures the user must be logged in to access this route
def logout():
    logout_user()  # Logs out the current user
    return redirect(url_for("auth.login"))  # Redirect to login page
