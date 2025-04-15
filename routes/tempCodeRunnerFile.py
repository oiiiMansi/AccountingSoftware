from flask import Blueprint, render_template, request, redirect, url_for, flash
import mysql.connector
from flask_login import login_required
from datetime import datetime


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
        gst = request.form["gst"]
        date = request.form["date"]

        # If the date is empty, set it to today's date
        if not date:
            date = datetime.today().strftime('%Y-%m-%d')

        cursor.execute("INSERT INTO expenses (expense_name, amount, category, gst, date) VALUES (%s, %s, %s, %s, %s)", 
                       (expense_name, amount, category, gst, date))
        conn.commit()
        flash("Expense added successfully!", "success")
        return redirect(url_for("expenses.expenses_page"))

    cursor.execute("SELECT * FROM expenses ORDER BY date DESC")
    expenses_list = cursor.fetchall()
    conn.close()

    return render_template("expenses.html", expenses=expenses_list)

# Edit Expense Route
@expenses.route("/edit_expense/<int:expense_id>", methods=["GET", "POST"])
@login_required
def edit_expense(expense_id):
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        expense_name = request.form["expense_name"]
        amount = request.form["amount"]
        category = request.form["category"]
        gst = request.form.get("gst", 0)
        date = request.form.get("date", datetime.today().strftime('%Y-%m-%d'))

        cursor.execute("""
            UPDATE expenses 
            SET expense_name=%s, amount=%s, category=%s, gst=%s, date=%s
            WHERE id=%s
        """, (expense_name, amount, category, gst, date, expense_id))
        conn.commit()
        flash("Expense updated successfully!", "success")
        return redirect(url_for("expenses.expenses_page"))

    cursor.execute("SELECT * FROM expenses WHERE id=%s", (expense_id,))
    expense = cursor.fetchone()
    conn.close()

    return render_template("edit_expense.html", expense=expense)

# Delete Expense Route
@expenses.route("/delete_expense/<int:expense_id>", methods=["GET"])
@login_required
def delete_expense(expense_id):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM expenses WHERE id=%s", (expense_id,))
    conn.commit()
    conn.close()

    flash("Expense deleted successfully!", "success")
    return redirect(url_for("expenses.expenses_page"))
