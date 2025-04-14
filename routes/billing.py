from flask import Blueprint, render_template, request, redirect, url_for, flash
import mysql.connector
from flask_login import login_required
from decimal import Decimal

# Define the Blueprint for billing
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
            # Get form data
            customer_name = request.form['customer_name']
            customer_number = request.form['customer_number']
            customer_address = request.form['customer_address']
            shipping_address = request.form['shipping_address']
            date = request.form['date']
            basic_amount = Decimal(request.form['basic_amount'])
            gst_type = request.form['gst_type']
            gst_percentage = Decimal(request.form['gst_percentage'])

            # Calculate GST and total amount
            gst_amount = (basic_amount * gst_percentage) / 100
            total_amount = basic_amount + gst_amount

            # Insert the bill into the database
            cursor.execute(
                "INSERT INTO bills (customer_name, customer_number, customer_address, shipping_address, date, basic_amount, gst_type, gst_percentage, gst_amount, total_amount) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (customer_name, customer_number, customer_address, shipping_address, date, basic_amount, gst_type, gst_percentage, gst_amount, total_amount)
            )
            conn.commit()
            flash("Invoice added successfully!", "success")

            return redirect(request.path)

        # Fetch all billing entries
        cursor.execute("SELECT * FROM bills ORDER BY date DESC")
        bills_list = cursor.fetchall()

    finally:
        cursor.close()
        conn.close()

    return render_template('billing.html', bills=bills_list)

# Delete a bill
@billing.route('/billing/delete/<int:bill_id>', methods=['GET'])
@login_required
def delete_bill(bill_id):
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM bills WHERE id = %s", (bill_id,))
        conn.commit()
        flash("Invoice deleted successfully!", "success")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('billing.billing_page'))

# Edit a bill
@billing.route('/billing/edit/<int:bill_id>', methods=['GET', 'POST'])
@login_required
def edit_bill(bill_id):
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    try:
        if request.method == 'POST':
            customer_name = request.form['customer_name']
            customer_number = request.form['customer_number']
            customer_address = request.form['customer_address']
            shipping_address = request.form['shipping_address']
            date = request.form['date']
            basic_amount = Decimal(request.form['basic_amount'])
            gst_type = request.form['gst_type']
            gst_percentage = Decimal(request.form['gst_percentage'])

            gst_amount = (basic_amount * gst_percentage) / 100
            total_amount = basic_amount + gst_amount

            cursor.execute("""
                UPDATE bills SET
                    customer_name=%s,
                    customer_number=%s,
                    customer_address=%s,
                    shipping_address=%s,
                    date=%s,
                    basic_amount=%s,
                    gst_type=%s,
                    gst_percentage=%s,
                    gst_amount=%s,
                    total_amount=%s
                WHERE id=%s
            """, (
                customer_name, customer_number, customer_address, shipping_address, date,
                basic_amount, gst_type, gst_percentage, gst_amount, total_amount, bill_id
            ))
            conn.commit()
            flash("Invoice updated successfully!", "success")
            return redirect(url_for('billing.billing_page'))

        # For GET request, show existing bill details
        cursor.execute("SELECT * FROM bills WHERE id = %s", (bill_id,))
        bill = cursor.fetchone()

    finally:
        cursor.close()
        conn.close()

    return render_template('edit_bill.html', bill=bill)
