from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
import mysql.connector
from decimal import Decimal
from datetime import datetime

# Define the Blueprint for sales
sales = Blueprint('sales', __name__)

# Database connection function
def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="roxanne",
        database="accounting"
    )

# Create non_billed_sales table if it doesn't exist
def create_non_billed_sales_table():
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS non_billed_sales (
            id INT AUTO_INCREMENT PRIMARY KEY,
            customer_name VARCHAR(255) NOT NULL,
            contact_number VARCHAR(50),
            item_details TEXT,
            amount DECIMAL(10,2) NOT NULL,
            date DATE NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.commit()
    except Exception as e:
        print(f"Error creating non_billed_sales table: {e}")
    finally:
        cursor.close()
        conn.close()

# Billing Route (GET and POST)
@sales.route('/billing', methods=['GET', 'POST'])
@login_required
def billing():
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)

    try:
        if request.method == 'POST':
            # Get form data
            customer_name = request.form['customer_name']
            amount = Decimal(request.form['basic_amount'])
            date = request.form['date']

            # Insert the bill into the database with only available columns
            cursor.execute(
                "INSERT INTO bills (customer_name, amount, date) VALUES (%s, %s, %s)",
                (customer_name, amount, date)
            )
            conn.commit()
            flash("Invoice added successfully!", "success")

            return redirect(url_for('sales.billing'))

        # Fetch all billing entries
        cursor.execute("SELECT * FROM bills ORDER BY date DESC")
        bills_list = cursor.fetchall()

    finally:
        cursor.close()
        conn.close()

    return render_template('billing.html', bills=bills_list)

# Without Billing Route (GET and POST)
@sales.route('/without_billing', methods=['GET', 'POST'])
@login_required
def without_billing():
    # Ensure the table exists
    create_non_billed_sales_table()
    
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    sales_list = []
    
    try:
        if request.method == 'POST':
            # Get form data
            customer_name = request.form['customer_name']
            contact_number = request.form['contact_number']
            item_details = request.form['item_details']
            amount = Decimal(request.form['amount'])
            date = request.form['date']
            notes = request.form.get('notes', '')

            # Insert into non_billed_sales table
            cursor.execute(
                "INSERT INTO non_billed_sales (customer_name, contact_number, item_details, amount, date, notes) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (customer_name, contact_number, item_details, amount, date, notes)
            )
            conn.commit()
            flash("Sale recorded successfully!", "success")
            return redirect(url_for('sales.without_billing'))
            
        # Fetch all non-billed sales
        cursor.execute("SELECT * FROM non_billed_sales ORDER BY date DESC")
        sales_list = cursor.fetchall()
        
    finally:
        cursor.close()
        conn.close()
        
    return render_template('without_billing.html', sales=sales_list)

# Delete non-billed sale
@sales.route('/delete_non_billed_sale/<int:sale_id>', methods=['GET'])
@login_required
def delete_non_billed_sale(sale_id):
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM non_billed_sales WHERE id = %s", (sale_id,))
        conn.commit()
        flash("Sale deleted successfully!", "success")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('sales.without_billing'))
    
# Edit non-billed sale - GET: Show form with current data, POST: Update data
@sales.route('/edit_non_billed_sale/<int:sale_id>', methods=['GET', 'POST'])
@login_required
def edit_non_billed_sale(sale_id):
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    try:
        if request.method == 'POST':
            # Get form data
            customer_name = request.form['customer_name']
            contact_number = request.form['contact_number']
            item_details = request.form['item_details']
            amount = Decimal(request.form['amount'])
            date = request.form['date']
            notes = request.form.get('notes', '')

            # Update the sale
            cursor.execute("""
                UPDATE non_billed_sales SET
                    customer_name = %s,
                    contact_number = %s,
                    item_details = %s,
                    amount = %s,
                    date = %s,
                    notes = %s
                WHERE id = %s
            """, (
                customer_name, contact_number, item_details, amount, date, notes, sale_id
            ))
            conn.commit()
            flash("Sale updated successfully!", "success")
            return redirect(url_for('sales.without_billing'))

        # For GET request, show existing sale details
        cursor.execute("SELECT * FROM non_billed_sales WHERE id = %s", (sale_id,))
        sale = cursor.fetchone()
        if not sale:
            flash("Sale not found", "error")
            return redirect(url_for('sales.without_billing'))

    finally:
        cursor.close()
        conn.close()

    return render_template('edit_non_billed_sale.html', sale=sale)

# Delete a bill
@sales.route('/delete_bill/<int:bill_id>', methods=['GET'])
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

    return redirect(url_for('sales.billing'))

# Edit a bill
@sales.route('/edit_bill/<int:bill_id>', methods=['GET', 'POST'])
@login_required
def edit_bill(bill_id):
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    try:
        if request.method == 'POST':
            customer_name = request.form['customer_name']
            amount = Decimal(request.form['basic_amount'])
            date = request.form['date']

            cursor.execute("""
                UPDATE bills SET
                    customer_name=%s,
                    amount=%s,
                    date=%s
                WHERE id=%s
            """, (customer_name, amount, date, bill_id))
            
            conn.commit()
            flash("Invoice updated successfully!", "success")
            return redirect(url_for('sales.billing'))

        # For GET request, show existing bill details
        cursor.execute("SELECT * FROM bills WHERE id = %s", (bill_id,))
        bill = cursor.fetchone()

    finally:
        cursor.close()
        conn.close()

    return render_template('edit_bill.html', bill=bill) 