from flask import Blueprint, render_template, request, redirect, url_for, flash
import mysql.connector
from flask_login import login_required, current_user
from mysql.connector import Error

budget_bp = Blueprint("budget", __name__, url_prefix="/budget")

# Change these to your actual DB credentials if needed
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "roxanne",
    "database": "accounting"
}

@budget_bp.route("/add", methods=["POST"])
@login_required
def add_budget():
    category = request.form.get("category")
    amount = request.form.get("amount")
    month = request.form.get("month")

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO budget (category, amount, month) VALUES (%s, %s, %s)", 
                       (category, amount, month))
        conn.commit()
        flash("Budget added successfully.", "success")
    except Error as e:
        flash(f"Database error: {e}", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for("budget.view_budget"))

@budget_bp.route("/view")
@login_required
def view_budget():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM budget")
        budgets = cursor.fetchall()
    except Error as e:
        flash(f"Database error: {e}", "danger")
        budgets = []
    finally:
        cursor.close()
        conn.close()

    return render_template("budgeting.html", budgets=budgets)
