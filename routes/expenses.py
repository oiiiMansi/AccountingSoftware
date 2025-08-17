from flask import Blueprint, render_template, request, redirect, url_for, flash
import mysql.connector
from flask_login import login_required
from datetime import datetime, timedelta
import calendar
from collections import defaultdict

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
        gst = request.form.get("gst", 0)
        date = request.form.get("date")

        # If the date is empty, set it to today's date
        if not date:
            date = datetime.today().strftime('%Y-%m-%d')  # Default to today's date

        # Insert the new expense into the database
        cursor.execute("INSERT INTO expenses (expense_name, amount, category, gst, date) VALUES (%s, %s, %s, %s, %s)", 
                       (expense_name, amount, category, gst, date))
        conn.commit()
        flash("Expense added successfully!", "success")
        return redirect(url_for("expenses.expenses_page"))

    # Get today's date for the date input default
    today_date = datetime.today().strftime('%Y-%m-%d')
    
    # Get current month data
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    # First day of current month
    first_day_current_month = datetime(current_year, current_month, 1).strftime('%Y-%m-%d')
    
    # Last day of current month
    last_day_current_month = datetime(
        current_year, 
        current_month, 
        calendar.monthrange(current_year, current_month)[1]
    ).strftime('%Y-%m-%d')
    
    # Calculate previous month
    first_day_prev_month = None
    last_day_prev_month = None
    
    if current_month == 1:
        prev_month = 12
        prev_year = current_year - 1
    else:
        prev_month = current_month - 1
        prev_year = current_year
    
    # First day of previous month
    first_day_prev_month = datetime(prev_year, prev_month, 1).strftime('%Y-%m-%d')
    
    # Last day of previous month
    last_day_prev_month = datetime(
        prev_year, 
        prev_month, 
        calendar.monthrange(prev_year, prev_month)[1]
    ).strftime('%Y-%m-%d')
    
    
    start_of_year = datetime(current_year, 1, 1).strftime('%Y-%m-%d')
    
    # Get all expenses sorted by date (newest first)
    cursor.execute("SELECT * FROM expenses ORDER BY date DESC")
    expenses_list = cursor.fetchall()
    
    # Calculate monthly and yearly totals
    cursor.execute("""
        SELECT SUM(amount) as total 
        FROM expenses 
        WHERE date BETWEEN %s AND %s
    """, (first_day_current_month, last_day_current_month))
    current_month_result = cursor.fetchone()
    current_month_total = current_month_result['total'] if current_month_result and current_month_result['total'] else 0
    
    cursor.execute("""
        SELECT SUM(amount) as total 
        FROM expenses 
        WHERE date BETWEEN %s AND %s
    """, (first_day_prev_month, last_day_prev_month))
    prev_month_result = cursor.fetchone()
    previous_month_total = prev_month_result['total'] if prev_month_result and prev_month_result['total'] else 0
    
    cursor.execute("""
        SELECT SUM(amount) as total 
        FROM expenses 
        WHERE date >= %s
    """, (start_of_year,))
    ytd_result = cursor.fetchone()
    ytd_total = ytd_result['total'] if ytd_result and ytd_result['total'] else 0
    
    # Calculate month-over-month change (percentage)
    if previous_month_total and previous_month_total > 0:
        month_change = round(((current_month_total - previous_month_total) / previous_month_total) * 100, 2)
    else:
        month_change = 0
    
    # Get expense data by category for chart
    cursor.execute("""
        SELECT category, SUM(amount) as total 
        FROM expenses 
        GROUP BY category 
        ORDER BY total DESC
    """)
    category_data = cursor.fetchall()
    
    expense_categories = []
    category_totals = []
    
    for cat in category_data:
        expense_categories.append(cat['category'])
        category_totals.append(float(cat['total']))
    
    conn.close()

    return render_template(
        "expenses.html", 
        expenses=expenses_list,
        today_date=today_date,
        current_month_total=current_month_total,
        previous_month_total=previous_month_total,
        ytd_total=ytd_total,
        month_change=month_change,
        expense_categories=expense_categories,
        category_totals=category_totals
    )

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
        date = request.form.get("date")

        # If date is not provided, use today's date
        if not date:
            date = datetime.today().strftime('%Y-%m-%d')

        # Update the expense in the database
        cursor.execute("""
            UPDATE expenses 
            SET expense_name=%s, amount=%s, category=%s, gst=%s, date=%s
            WHERE id=%s
        """, (expense_name, amount, category, gst, date, expense_id))
        conn.commit()
        flash("Expense updated successfully!", "success")
        return redirect(url_for("expenses.expenses_page"))

    # Fetch the expense from the database
    cursor.execute("SELECT * FROM expenses WHERE id=%s", (expense_id,))
    expense = cursor.fetchone()
    
    # Get list of expense categories for dropdown
    cursor.execute("SELECT DISTINCT category FROM expenses ORDER BY category")
    categories = cursor.fetchall()
    
    conn.close()

    return render_template("edit_expense.html", expense=expense, categories=categories)

# Delete Expense Route
@expenses.route("/delete_expense/<int:expense_id>", methods=["GET"])
@login_required
def delete_expense(expense_id):
    conn = connect_db()
    cursor = conn.cursor()

    # Delete the expense from the database
    cursor.execute("DELETE FROM expenses WHERE id=%s", (expense_id,))
    conn.commit()
    conn.close()

    flash("Expense deleted successfully!", "success")
    return redirect(url_for("expenses.expenses_page"))
