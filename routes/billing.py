from flask import Blueprint, render_template, request, redirect, url_for, flash
import mysql.connector
from flask_login import login_required

billing = Blueprint('billing', __name__)




def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="roxanne",
        database="accounting"
    )

@billing.route('/billing', methods=['GET', 'POST'])
@login_required
def billing_page():
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)

    try:
        if request.method == 'POST':
            customer_name = request.form['customer_name']
            amount = request.form['amount']

            cursor.execute("INSERT INTO bills (customer_name, amount) VALUES (%s, %s)", 
                           (customer_name, amount))
            conn.commit()
            flash("Invoice added successfully!", "success")
            return redirect(url_for('billing.billing_page'))

        cursor.execute("SELECT * FROM bills ORDER BY date DESC")
        bills_list = cursor.fetchall()

    finally:
        cursor.close()
        conn.close()

    return render_template('billing.html', bills=bills_list)
