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

# Create purchase table if it doesn't exist
def create_purchase_table():
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchases (
            id INT AUTO_INCREMENT PRIMARY KEY,
            vendor_name VARCHAR(255) NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            date DATE NOT NULL,
            item_details TEXT NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.commit()
    except Exception as e:
        print(f"Error creating purchases table: {e}")
    finally:
        cursor.close()
        conn.close()

# Create billed purchase table if it doesn't exist
def create_billed_purchase_table():
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS billed_purchases (
            id INT AUTO_INCREMENT PRIMARY KEY,
            vendor_name VARCHAR(255) NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            gst_type ENUM('CGST_SGST', 'IGST') DEFAULT 'CGST_SGST',
            gst_percentage DECIMAL(5,2) DEFAULT 18.00,
            date DATE NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.commit()
    except Exception as e:
        print(f"Error creating billed_purchases table: {e}")
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

# Purchase dashboard page - Direct HTML return
@sales.route('/purchase', methods=['GET'])
@login_required
def purchase():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Purchase Options - KK Enterprises</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                background-color: #f5f5f5;
            }
            .container {
                max-width: 800px;
                margin: 50px auto;
                padding: 30px;
                background-color: #fff;
                border-radius: 10px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
                text-align: center;
            }
            h1 {
                color: #333;
                margin-bottom: 30px;
            }
            .options {
                display: flex;
                justify-content: center;
                gap: 30px;
                margin-top: 30px;
            }
            .option-card {
                background-color: #fff;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 25px;
                width: 250px;
                text-align: center;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            }
            .option-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            }
            .option-card h2 {
                color: #333;
                margin-top: 0;
            }
            .option-card p {
                color: #666;
                margin-bottom: 20px;
            }
            .btn {
                display: inline-block;
                background-color: #ffa500;
                color: white;
                padding: 12px 24px;
                border-radius: 5px;
                text-decoration: none;
                font-weight: bold;
                transition: background-color 0.3s ease;
            }
            .btn:hover {
                background-color: #e69400;
            }
            .home-link {
                display: block;
                margin-top: 30px;
                color: #666;
                text-decoration: none;
            }
            .home-link:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Purchase Management</h1>
            
            <div class="options">
                <div class="option-card">
                    <h2>Billed Purchase</h2>
                    <p>Record purchases with GST. Use for official vendors that provide GST invoices.</p>
                    <a href="/sales/billed_purchase" class="btn">Go to Billed Purchase</a>
                </div>
                
                <div class="option-card">
                    <h2>Non-Billed Purchase</h2>
                    <p>Record simple purchases without GST. Ideal for small vendors or cash purchases.</p>
                    <a href="/sales/non_billed_purchase" class="btn">Go to Non-Billed Purchase</a>
                </div>
            </div>
            
            <a href="/" class="home-link">← Back to Dashboard</a>
        </div>
    </body>
    </html>
    """

# Billed Purchase Route (with GST)
@sales.route('/billed_purchase', methods=['GET', 'POST'])
@login_required
def billed_purchase():
    # Ensure the table exists
    create_billed_purchase_table()
    
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    purchases_list = []
    
    try:
        if request.method == 'POST':
            # Get form data
            vendor_name = request.form['vendor_name']
            amount = Decimal(request.form['basic_amount'])
            gst_type = request.form['gst_type']
            gst_percentage = Decimal(request.form['gst_percentage'])
            date = request.form['date']
            description = request.form.get('description', '')

            # Insert into billed_purchases table
            cursor.execute(
                "INSERT INTO billed_purchases (vendor_name, amount, gst_type, gst_percentage, date, description) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (vendor_name, amount, gst_type, gst_percentage, date, description)
            )
            conn.commit()
            flash("Billed purchase recorded successfully!", "success")
            return redirect(url_for('sales.billed_purchase'))
            
        # Fetch all billed purchases
        cursor.execute("SELECT * FROM billed_purchases ORDER BY date DESC")
        purchases_list = cursor.fetchall()
        
    finally:
        cursor.close()
        conn.close()
        
    return render_template('billed_purchase.html', purchases=purchases_list)

# Non-Billed Purchase Route
@sales.route('/non_billed_purchase', methods=['GET', 'POST'])
@login_required
def non_billed_purchase():
    # Ensure the table exists
    create_purchase_table()
    
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    purchases = []
    
    try:
        if request.method == 'POST':
            # Get form data
            vendor_name = request.form['vendor_name']
            amount = Decimal(request.form['amount'])
            date = request.form['date']
            item_details = request.form['item_details']
            notes = request.form.get('notes', '')
            
            # Insert purchase record
            cursor.execute(
                "INSERT INTO purchases (vendor_name, amount, date, item_details, notes) VALUES (%s, %s, %s, %s, %s)",
                (vendor_name, amount, date, item_details, notes)
            )
            conn.commit()
            flash("Purchase recorded successfully!", "success")
        
        # Fetch all purchases
        cursor.execute("SELECT * FROM purchases ORDER BY date DESC")
        purchases = cursor.fetchall()
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
    finally:
        cursor.close()
        conn.close()
    
    return render_template('non_billed_purchase.html', purchases=purchases)

# Edit billed purchase
@sales.route('/edit_billed_purchase/<int:purchase_id>', methods=['GET', 'POST'])
@login_required
def edit_billed_purchase(purchase_id):
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    
    try:
        if request.method == 'POST':
            # Get form data
            vendor_name = request.form['vendor_name']
            amount = Decimal(request.form['basic_amount'])
            gst_type = request.form['gst_type']
            gst_percentage = Decimal(request.form['gst_percentage'])
            date = request.form['date']
            description = request.form.get('description', '')
            
            # Update purchase
            cursor.execute("""
                UPDATE billed_purchases SET
                    vendor_name = %s,
                    amount = %s,
                    gst_type = %s,
                    gst_percentage = %s,
                    date = %s,
                    description = %s
                WHERE id = %s
            """, (vendor_name, amount, gst_type, gst_percentage, date, description, purchase_id))
            conn.commit()
            flash("Purchase updated successfully!", "success")
            return redirect(url_for('sales.billed_purchase'))
            
        # For GET request, show existing purchase
        cursor.execute("SELECT * FROM billed_purchases WHERE id = %s", (purchase_id,))
        purchase = cursor.fetchone()
        if not purchase:
            flash("Purchase not found", "error")
            return redirect(url_for('sales.billed_purchase'))
            
        return render_template('edit_billed_purchase.html', purchase=purchase)
    finally:
        cursor.close()
        conn.close()

# Delete billed purchase
@sales.route('/delete_billed_purchase/<int:purchase_id>', methods=['GET'])
@login_required
def delete_billed_purchase(purchase_id):
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM billed_purchases WHERE id = %s", (purchase_id,))
        conn.commit()
        flash("Purchase deleted successfully!", "success")
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
    finally:
        cursor.close()
        conn.close()
        
    return redirect(url_for('sales.billed_purchase'))

# Edit non-billed purchase
@sales.route('/edit_non_billed_purchase/<int:purchase_id>', methods=['GET', 'POST'])
@login_required
def edit_non_billed_purchase(purchase_id):
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    
    try:
        if request.method == 'POST':
            # Get form data
            vendor_name = request.form['vendor_name']
            amount = Decimal(request.form['amount'])
            date = request.form['date']
            item_details = request.form['item_details']
            notes = request.form.get('notes', '')
            
            # Update purchase
            cursor.execute("""
                UPDATE purchases SET
                    vendor_name = %s,
                    amount = %s,
                    date = %s,
                    item_details = %s,
                    notes = %s
                WHERE id = %s
            """, (vendor_name, amount, date, item_details, notes, purchase_id))
            conn.commit()
            flash("Purchase updated successfully!", "success")
            return redirect(url_for('sales.non_billed_purchase'))
            
        # For GET request, show existing purchase
        cursor.execute("SELECT * FROM purchases WHERE id = %s", (purchase_id,))
        purchase = cursor.fetchone()
        if not purchase:
            flash("Purchase not found", "error")
            return redirect(url_for('sales.non_billed_purchase'))
            
        return render_template('edit_non_billed_purchase.html', purchase=purchase)
    finally:
        cursor.close()
        conn.close()

# Delete non-billed purchase
@sales.route('/delete_non_billed_purchase/<int:purchase_id>', methods=['GET'])
@login_required
def delete_non_billed_purchase(purchase_id):
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM purchases WHERE id = %s", (purchase_id,))
        conn.commit()
        flash("Purchase deleted successfully!", "success")
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
    finally:
        cursor.close()
        conn.close()
        
    return redirect(url_for('sales.non_billed_purchase')) 