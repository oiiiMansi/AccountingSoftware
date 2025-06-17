from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
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
    # Skip registration page if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == "POST":
        try:
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

                # Insert the new user into the database with password_hash field
                cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
                               (username, hashed_password, role))
                conn.commit()
                flash("User registered successfully! Please log in.", "success")
                return redirect(url_for("auth.login"))

            except mysql.connector.Error as err:
                flash(f"Error: {err}", "danger")
            finally:
                cursor.close()
                conn.close()
        except KeyError:
            flash("Please fill in all required fields.", "danger")
            return redirect(url_for("auth.register"))

    return render_template("register.html")


# ✅ Login Route
@auth.route("/login", methods=["GET", "POST"])
def  login_view():
    # Skip login page if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    # For GET, capture ?next from URL
    next_page = request.args.get("next")

    if request.method == "POST":
        try:
            username = request.form["username"]
            password = request.form["password"]
            remember = "remember" in request.form

            # Basic form validation
            if not username or not password:
                flash("Please enter both username and password.", "danger")
                return redirect(url_for("auth.login_view")
)

            conn = connect_db()
            cursor = conn.cursor(dictionary=True)

            try:
                # Debug print for troubleshooting
                cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
                user = cursor.fetchone()
                
                if user:
                    # Get the password hash value for debugging
                    password_hash = user.get("password_hash", "MISSING")
                    
                    # Check if the password hash exists and verify it
                    if password_hash and check_password_hash(password_hash, password):
                        user_obj = User(user["id"], user["username"], user["role"])
                        login_user(user_obj, remember=remember)
                        
                        # Redirect to the next page or home if not specified
                        next_page = request.form.get("next") or next_page
                        if not next_page or next_page == "None" or "//" in next_page:
                            next_page = url_for("home")
                        flash(f"Welcome back, {username}!", "success")
                        return redirect(next_page)
                    else:
                        flash("Invalid credentials! Please check your password.", "danger")
                else:
                    flash("User not found! Please check your username.", "danger")

            except mysql.connector.Error as err:
                flash(f"Error: {err}", "danger")
            finally:
                cursor.close()
                conn.close()
        except KeyError:
            flash("Please fill in all required fields.", "danger")
            return redirect(url_for("auth.login"))

    return render_template("login.html", next_page=next_page)


# ✅ Logout Route
@auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have successfully logged out.", "success")
    return redirect(url_for("auth.login_view"))
