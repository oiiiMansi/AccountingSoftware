from flask import Blueprint, render_template, request, redirect, url_for, flash
import mysql.connector
from flask_login import login_required

expenses = Blueprint("expenses", __name__)

# Database connection
def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="roxanne",
        database="accounting"
    )

@expenses.route("/expenses", methods=["GET", "POST"])
@login_required
def expenses_page():
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        expense_name = request.form["expense_name"]
        amount = request.form["amount"]
        category = request.form["category"]

        cursor.execute("INSERT INTO expenses (expense_name, amount, category) VALUES (%s, %s, %s)", 
                       (expense_name, amount, category))
        conn.commit()
        flash("Expense added successfully!", "success")
        return redirect(url_for("expenses.expenses_page"))

    cursor.execute("SELECT * FROM expenses ORDER BY created_at DESC")
    expenses_list = cursor.fetchall()
    conn.close()

    return render_template("expenses.html", expenses=expenses_list)
