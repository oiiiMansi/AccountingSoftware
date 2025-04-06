from flask import Blueprint, render_template, request, redirect, url_for, flash
import mysql.connector
from flask_login import login_required

billing = Blueprint('billing', __name__)

# Database connection function
def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="roxanne",
        database="accounting"
    )

# Billing Route (GET and POST)
@billing.route('/billing', methods=['GET', 'POST'])
@login_required
def billing_page():
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)

    try:
        if request.method == 'POST':
            customer_name = request.form['customer_name']
            amount = request.form['amount']

            cursor.execute(
                "INSERT INTO bills (customer_name, amount) VALUES (%s, %s)",
                (customer_name, amount)
            )
            conn.commit()
            flash("Invoice added successfully!", "success")

            # Prevent form resubmission on refresh
            return redirect(request.path)

        # Fetch all billing entries
        cursor.execute("SELECT * FROM bills ORDER BY date DESC")
        bills_list = cursor.fetchall()

    finally:
        cursor.close()
        conn.close()

    return render_template('billing.html', bills=bills_list)
