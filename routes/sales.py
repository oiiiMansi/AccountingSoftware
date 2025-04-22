from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
import mysql.connector
from decimal import Decimal
from datetime import datetime
import logging

# Define the Blueprint for sales
sales = Blueprint('sales', __name__)

# Add this at the top of your file
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        # Check if quantity column exists
        cursor.execute("SHOW COLUMNS FROM non_billed_sales LIKE 'quantity'")
        quantity_exists = cursor.fetchone()
        
        if not quantity_exists:
            cursor.execute("ALTER TABLE non_billed_sales ADD COLUMN quantity INT DEFAULT 1 AFTER item_details")
            conn.commit()
            print("Added quantity column to non_billed_sales table")
            
        # If table doesn't exist, create it with quantity column
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS non_billed_sales (
            id INT AUTO_INCREMENT PRIMARY KEY,
            customer_name VARCHAR(255) NOT NULL,
            contact_number VARCHAR(50),
            item_details TEXT,
            quantity INT DEFAULT 1,
            amount DECIMAL(10,2) NOT NULL,
            date DATE NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.commit()
    except Exception as e:
        print(f"Error creating/updating non_billed_sales table: {e}")
    finally:
        cursor.close()
        conn.close()

# Create purchase table if it doesn't exist
def create_purchase_table():
    conn = connect_db()
    cursor = conn.cursor()
    try:
        # Check if quantity column exists
        cursor.execute("SHOW COLUMNS FROM purchases LIKE 'quantity'")
        quantity_exists = cursor.fetchone()
        
        if not quantity_exists:
            cursor.execute("ALTER TABLE purchases ADD COLUMN quantity INT DEFAULT 1 AFTER amount")
            conn.commit()
            print("Added quantity column to purchases table")
            
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchases (
            id INT AUTO_INCREMENT PRIMARY KEY,
            vendor_name VARCHAR(255) NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            quantity INT DEFAULT 1,
            date DATE NOT NULL,
            item_details TEXT NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.commit()
    except Exception as e:
        print(f"Error creating/updating purchases table: {e}")
    finally:
        cursor.close()
        conn.close()

# Create billed purchase table if it doesn't exist
def create_billed_purchase_table():
    conn = connect_db()
    cursor = conn.cursor()
    try:
        # Check if quantity column exists
        cursor.execute("SHOW COLUMNS FROM billed_purchases LIKE 'quantity'")
        quantity_exists = cursor.fetchone()
        
        if not quantity_exists:
            cursor.execute("ALTER TABLE billed_purchases ADD COLUMN quantity INT DEFAULT 1 AFTER amount")
            conn.commit()
            print("Added quantity column to billed_purchases table")
            
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS billed_purchases (
            id INT AUTO_INCREMENT PRIMARY KEY,
            vendor_name VARCHAR(255) NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            quantity INT DEFAULT 1,
            gst_type ENUM('CGST_SGST', 'IGST') DEFAULT 'CGST_SGST',
            gst_percentage DECIMAL(5,2) DEFAULT 18.00,
            date DATE NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.commit()
    except Exception as e:
        print(f"Error creating/updating billed_purchases table: {e}")
    finally:
        cursor.close()
        conn.close()

# Billing Route (GET and POST)
@sales.route('/billing', methods=['GET', 'POST'])
@login_required
def billing():
    # Ensure table has required columns
    update_bills_table()
    update_sales_tables()
    
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)

    try:
        if request.method == 'POST':
            # Debug: Log all form data (complete dump)
            form_data_str = str(request.form.to_dict())
            logger.info(f"Complete form data: {form_data_str}")
            
            # Get form data
            customer_name = request.form.get('customer_name', '')
            amount = Decimal(request.form.get('basic_amount', 0))
            quantity = int(request.form.get('quantity', 1))
            date = request.form.get('date', '')
            
            # Get GST-related fields
            gst_type = request.form.get('gst_type', '')
            gst_percentage = Decimal(request.form.get('gst_percentage', 0))
            
            # Calculate GST and total amount
            gst_amount = 0
            if gst_percentage > 0:
                gst_amount = amount * gst_percentage / 100
            total_amount = amount + gst_amount
            
            # Force use request.form.get for payment_type to debug
            raw_payment_type = request.form.get('payment_type')
            logger.info(f"Raw payment_type from request.form.get: {raw_payment_type}")
            
            # Check if payment_type exists in any form field (case-insensitive)
            payment_type_found = False
            for key, value in request.form.items():
                if key.lower() == 'payment_type' and value:
                    payment_type_found = True
                    logger.info(f"Found payment_type in field {key} with value {value}")
            
            # Determine payment_type and status
            # Explicitly check if the value is "Credit", case-sensitive
            payment_type = 'Cash'  # Default
            if raw_payment_type == 'Credit':
                payment_type = 'Credit'
                logger.info("Setting payment_type to Credit")
            
            # Check for test form submission (which we know works)
            if customer_name == 'Test Credit Customer' and raw_payment_type == 'Credit':
                payment_type = 'Credit'
                logger.info("This is a test credit sale - forcing Credit payment_type")
            
            # Set payment status based on payment type
            payment_status = 'Pending' if payment_type == 'Credit' else 'Paid'
            
            # CRITICAL: Log the final decision
            logger.info(f"FINAL DECISION: payment_type={payment_type}, payment_status={payment_status}")
            
            # Get other form fields
            customer_number = request.form.get('customer_number', '')
            customer_address = request.form.get('customer_address', '')
            shipping_address = request.form.get('shipping_address', '')
            
            # Insert with explicit payment_type value and GST fields
            sql = """
            INSERT INTO bills 
            (customer_name, customer_number, customer_address, shipping_address, 
            basic_amount, quantity, gst_type, gst_percentage, gst_amount, total_amount,
            payment_type, payment_status, date) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            params = (
                customer_name, customer_number, customer_address, shipping_address,
                amount, quantity, gst_type, gst_percentage, gst_amount, total_amount,
                payment_type, payment_status, date
            )
            
            cursor.execute(sql, params)
            conn.commit()
            
            # Show different message based on payment type
            if payment_type == 'Credit':
                flash(f"Credit sale added successfully! Value stored: {payment_type}", "success")
            else:
                flash(f"Invoice added successfully! Value stored: {payment_type}", "success")

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
    # Ensure tables exist with proper schema
    create_non_billed_sales_table()
    update_transactions_table()
    update_sales_tables()
    
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    sales_list = []
    
    try:
        if request.method == 'POST':
            # Debug: Log all form data
            logger.info("Form data received in without_billing route:")
            for key, value in request.form.items():
                logger.info(f"  {key}: {value}")
            
            # Get form data
            customer_name = request.form['customer_name']
            contact_number = request.form['contact_number']
            item_details = request.form['item_details']
            quantity = int(request.form.get('quantity', 1))
            amount = Decimal(request.form['amount'])
            date = request.form['date']
            notes = request.form.get('notes', '')
            
            # Get payment_type with logging
            payment_type = request.form.get('payment_type')
            logger.info(f"Raw payment_type value: {payment_type}")
            
            # Sanitize and validate payment_type
            if payment_type not in ['Cash', 'Credit']:
                logger.warning(f"Invalid payment_type: {payment_type}, defaulting to Cash")
                payment_type = 'Cash'
            
            # Set payment status based on payment type
            payment_status = 'Pending' if payment_type == 'Credit' else 'Paid'
            logger.info(f"Final payment_type: {payment_type}, payment_status: {payment_status}")

            # Start a transaction
            conn.autocommit = False
            
            try:
                # Debug: Print SQL query and parameters
                sql = """
                INSERT INTO non_billed_sales 
                (customer_name, contact_number, item_details, quantity, amount, 
                payment_type, payment_status, date, notes) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                params = (customer_name, contact_number, item_details, quantity, amount, 
                        payment_type, payment_status, date, notes)
                
                logger.info(f"Executing SQL: {sql}")
                logger.info(f"With parameters: {params}")
                
                # Insert into non_billed_sales table
                cursor.execute(sql, params)
                
                # Get the ID of the inserted sale
                sale_id = cursor.lastrowid
                logger.info(f"Inserted sale with ID: {sale_id}")
                
                # Add to transactions as credit
                description = f"Sale to {customer_name}: {item_details} (Qty: {quantity})"
                cursor.execute(
                    """INSERT INTO transactions 
                       (description, amount, date, transaction_type, reference_id, reference_type) 
                       VALUES (%s, %s, %s, 'credit', %s, 'non_billed_sale')""",
                    (description, amount, date, sale_id)
                )
                
                # Commit both operations
                conn.commit()
                logger.info("Transaction committed successfully")
                
                # Show different message based on payment type
                if payment_type == 'Credit':
                    flash("Credit sale recorded successfully!", "success")
                else:
                    flash("Sale recorded successfully!", "success")
                    
            except Exception as e:
                # Rollback on error
                conn.rollback()
                logger.error(f"Error in database operation: {str(e)}")
                flash(f"Error: {str(e)}", "error")
                
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
        # Start transaction
        conn.autocommit = False
        
        # Delete the transaction associated with this sale first
        cursor.execute("DELETE FROM transactions WHERE reference_id = %s AND reference_type = 'non_billed_sale'", (sale_id,))
        
        # Now delete the sale
        cursor.execute("DELETE FROM non_billed_sales WHERE id = %s", (sale_id,))
        
        # Commit the transaction
        conn.commit()
        flash("Sale deleted successfully!", "success")
    except Exception as e:
        # Rollback on error
        conn.rollback()
        flash(f"Error deleting sale: {str(e)}", "error")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('sales.without_billing'))
    
# Edit non-billed sale
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
            quantity = int(request.form.get('quantity', 1))
            amount = Decimal(request.form['amount'])
            date = request.form['date']
            notes = request.form.get('notes', '')

            # Begin transaction
            conn.autocommit = False
            
            try:
                # Update the sale record
                cursor.execute("""
                    UPDATE non_billed_sales SET
                        customer_name = %s,
                        contact_number = %s,
                        item_details = %s,
                        quantity = %s,
                        amount = %s,
                        date = %s,
                        notes = %s
                    WHERE id = %s
                """, (
                    customer_name, contact_number, item_details, quantity, amount, date, notes, sale_id
                ))
                
                # Update corresponding transaction record
                description = f"Sale to {customer_name}: {item_details} (Qty: {quantity})"
                cursor.execute("""
                    UPDATE transactions SET
                        description = %s,
                        amount = %s,
                        date = %s
                    WHERE reference_id = %s AND reference_type = 'non_billed_sale'
                """, (description, amount, date, sale_id))
                
                conn.commit()
                flash("Sale updated successfully!", "success")
            except Exception as e:
                conn.rollback()
                flash(f"Error updating sale: {str(e)}", "error")
                
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
        # Start transaction
        conn.autocommit = False
        
        # Delete the transaction associated with this bill first
        cursor.execute("DELETE FROM transactions WHERE reference_id = %s AND reference_type = 'bill'", (bill_id,))
        
        # Now delete the bill
        cursor.execute("DELETE FROM bills WHERE id = %s", (bill_id,))
        
        # Commit the transaction
        conn.commit()
        flash("Invoice deleted successfully!", "success")
    except Exception as e:
        # Rollback on error
        conn.rollback()
        flash(f"Error deleting invoice: {str(e)}", "error")
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
            # Get form data
            customer_name = request.form['customer_name']
            basic_amount = Decimal(request.form['basic_amount'])
            quantity = int(request.form.get('quantity', 1))
            date = request.form['date']
            # Get other form fields if available
            customer_number = request.form.get('customer_number', '')
            customer_address = request.form.get('customer_address', '')
            shipping_address = request.form.get('shipping_address', '')
            gst_type = request.form.get('gst_type', '')
            gst_percentage = Decimal(request.form.get('gst_percentage', 0))

            # Calculate GST and total amount
            gst_amount = 0
            if gst_percentage > 0:
                gst_amount = basic_amount * gst_percentage / 100
            total_amount = basic_amount + gst_amount

            # Begin transaction
            conn.autocommit = False
            
            try:
                # Update the bill
                cursor.execute("""
                    UPDATE bills SET
                        customer_name = %s,
                        customer_number = %s,
                        customer_address = %s,
                        shipping_address = %s,
                        basic_amount = %s,
                        quantity = %s,
                        gst_type = %s,
                        gst_percentage = %s,
                        gst_amount = %s,
                        total_amount = %s,
                        date = %s
                    WHERE id = %s
                """, (
                    customer_name, customer_number, customer_address, shipping_address,
                    basic_amount, quantity, gst_type, gst_percentage, gst_amount, total_amount, date, bill_id
                ))
                
                # Check if there's a corresponding transaction
                cursor.execute("SELECT id FROM transactions WHERE reference_id = %s AND reference_type = 'bill'", (bill_id,))
                transaction = cursor.fetchone()
                
                if transaction:
                    description = f"Bill from {customer_name} (Qty: {quantity})"
                    cursor.execute("""
                        UPDATE transactions SET
                            description = %s,
                            amount = %s,
                            date = %s
                        WHERE reference_id = %s AND reference_type = 'bill'
                    """, (description, total_amount, date, bill_id))
                
                conn.commit()
                flash("Bill updated successfully!", "success")
            except Exception as e:
                conn.rollback()
                flash(f"Error updating bill: {str(e)}", "error")
                
            return redirect(url_for('sales.billing'))

        # For GET request, show existing bill details
        cursor.execute("SELECT * FROM bills WHERE id = %s", (bill_id,))
        bill = cursor.fetchone()
        if not bill:
            flash("Bill not found", "error")
            return redirect(url_for('sales.billing'))

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
    # Ensure tables exist with proper schema
    create_billed_purchase_table()
    update_transactions_table()
    
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    purchases_list = []
    
    try:
        if request.method == 'POST':
            # Get form data
            vendor_name = request.form['vendor_name']
            amount = Decimal(request.form['basic_amount'])
            quantity = int(request.form.get('quantity', 1))
            gst_type = request.form.get('gst_type', 'CGST_SGST')
            gst_percentage = Decimal(request.form.get('gst_percentage', 18.00))
            date = request.form['date']
            description = request.form.get('description', '')
            
            # Calculate total amount with GST
            total_amount = amount * (1 + gst_percentage/100)

            # Start transaction
            conn.autocommit = False
            
            try:
                # Insert into billed_purchases table
                cursor.execute(
                    """INSERT INTO billed_purchases 
                    (vendor_name, amount, quantity, gst_type, gst_percentage, date, description) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (vendor_name, amount, quantity, gst_type, gst_percentage, date, description)
                )
                
                # Get the ID of the inserted purchase
                purchase_id = cursor.lastrowid
                
                # Add to transactions as debit
                trans_description = f"Purchase from {vendor_name}: {description} (Qty: {quantity})"
                cursor.execute(
                    """INSERT INTO transactions 
                    (description, amount, date, transaction_type, reference_id, reference_type) 
                    VALUES (%s, %s, %s, 'debit', %s, 'billed_purchase')""",
                    (trans_description, total_amount, date, purchase_id)
                )
                
                # Commit both operations
                conn.commit()
                flash("Purchase recorded successfully!", "success")
            except Exception as e:
                # Rollback on error
                conn.rollback()
                flash(f"Error: {str(e)}", "error")
            
            return redirect(url_for('sales.billed_purchase'))
        
        # Fetch all billed purchases
        cursor.execute("SELECT * FROM billed_purchases ORDER BY date DESC")
        purchases_list = cursor.fetchall()
        
    finally:
        cursor.close()
        conn.close()
        
    return render_template('billed_purchase.html', purchases=purchases_list)

# Non-Billed Purchase Route (without GST)
@sales.route('/non_billed_purchase', methods=['GET', 'POST'])
@login_required
def non_billed_purchase():
    # Ensure tables exist with proper schema
    create_purchase_table()
    update_transactions_table()
    
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    purchases_list = []
    
    try:
        if request.method == 'POST':
            # Get form data
            vendor_name = request.form['vendor_name']
            amount = Decimal(request.form['amount'])
            quantity = int(request.form.get('quantity', 1))
            date = request.form['date']
            item_details = request.form['item_details']
            notes = request.form.get('notes', '')
            
            # Start transaction
            conn.autocommit = False
            
            try:
                # Insert into purchases table
                cursor.execute(
                    """INSERT INTO purchases 
                    (vendor_name, amount, quantity, date, item_details, notes) 
                    VALUES (%s, %s, %s, %s, %s, %s)""",
                    (vendor_name, amount, quantity, date, item_details, notes)
                )
                
                # Get the ID of the inserted purchase
                purchase_id = cursor.lastrowid
                
                # Add to transactions as debit
                description = f"Purchase from {vendor_name}: {item_details} (Qty: {quantity})"
                cursor.execute(
                    """INSERT INTO transactions 
                    (description, amount, date, transaction_type, reference_id, reference_type) 
                    VALUES (%s, %s, %s, 'debit', %s, 'purchase')""",
                    (description, amount, date, purchase_id)
                )
                
                # Commit both operations
                conn.commit()
                flash("Purchase recorded successfully!", "success")
            except Exception as e:
                # Rollback on error
                conn.rollback()
                flash(f"Error: {str(e)}", "error")
            
            return redirect(url_for('sales.non_billed_purchase'))
            
        # Fetch all non-billed purchases
        cursor.execute("SELECT * FROM purchases ORDER BY date DESC")
        purchases_list = cursor.fetchall()
        
    finally:
        cursor.close()
        conn.close()
        
    return render_template('non_billed_purchase.html', purchases=purchases_list)

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
            quantity = int(request.form.get('quantity', 1))
            gst_type = request.form.get('gst_type', 'CGST_SGST')
            gst_percentage = Decimal(request.form.get('gst_percentage', 18.00))
            date = request.form['date']
            description = request.form.get('description', '')
            
            # Calculate total amount with GST
            total_amount = amount * (1 + gst_percentage/100)
            
            # Begin transaction
            conn.autocommit = False
            
            try:
                # Update the purchase
                cursor.execute("""
                    UPDATE billed_purchases SET
                        vendor_name = %s,
                        amount = %s,
                        quantity = %s,
                        gst_type = %s,
                        gst_percentage = %s,
                        date = %s,
                        description = %s
                    WHERE id = %s
                """, (
                    vendor_name, amount, quantity, gst_type, gst_percentage, date, description, purchase_id
                ))
                
                # Update corresponding transaction record
                trans_description = f"Purchase from {vendor_name}: {description} (Qty: {quantity})"
                cursor.execute("""
                    UPDATE transactions SET
                        description = %s,
                        amount = %s,
                        date = %s
                    WHERE reference_id = %s AND reference_type = 'billed_purchase'
                """, (trans_description, total_amount, date, purchase_id))
                
                conn.commit()
                flash("Purchase updated successfully!", "success")
            except Exception as e:
                conn.rollback()
                flash(f"Error updating purchase: {str(e)}", "error")
                
            return redirect(url_for('sales.billed_purchase'))
            
        # For GET request, show existing purchase details
        cursor.execute("SELECT * FROM billed_purchases WHERE id = %s", (purchase_id,))
        purchase = cursor.fetchone()
        if not purchase:
            flash("Purchase not found", "error")
            return redirect(url_for('sales.billed_purchase'))
            
    finally:
        cursor.close()
        conn.close()
        
    return render_template('edit_billed_purchase.html', purchase=purchase)

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
            quantity = int(request.form.get('quantity', 1))
            date = request.form['date']
            item_details = request.form['item_details']
            notes = request.form.get('notes', '')
            
            # Begin transaction
            conn.autocommit = False
            
            try:
                # Update the purchase
                cursor.execute("""
                    UPDATE purchases SET
                        vendor_name = %s,
                        amount = %s,
                        quantity = %s,
                        date = %s,
                        item_details = %s,
                        notes = %s
                    WHERE id = %s
                """, (
                    vendor_name, amount, quantity, date, item_details, notes, purchase_id
                ))
                
                # Update corresponding transaction record
                description = f"Purchase from {vendor_name}: {item_details} (Qty: {quantity})"
                cursor.execute("""
                    UPDATE transactions SET
                        description = %s,
                        amount = %s,
                        date = %s
                    WHERE reference_id = %s AND reference_type = 'purchase'
                """, (description, amount, date, purchase_id))
                
                conn.commit()
                flash("Purchase updated successfully!", "success")
            except Exception as e:
                conn.rollback()
                flash(f"Error updating purchase: {str(e)}", "error")
                
            return redirect(url_for('sales.non_billed_purchase'))
            
        # For GET request, show existing purchase details
        cursor.execute("SELECT * FROM purchases WHERE id = %s", (purchase_id,))
        purchase = cursor.fetchone()
        if not purchase:
            flash("Purchase not found", "error")
            return redirect(url_for('sales.non_billed_purchase'))
            
    finally:
        cursor.close()
        conn.close()
        
    return render_template('edit_non_billed_purchase.html', purchase=purchase)

def update_transactions_table():
    """Add required columns to transactions table if they don't exist"""
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        # Check if transaction_type column exists
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.columns 
            WHERE table_name = 'transactions' 
            AND column_name = 'transaction_type'
        """)
        has_transaction_type = cursor.fetchone()[0] > 0
        
        # Check if reference_id column exists
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.columns 
            WHERE table_name = 'transactions' 
            AND column_name = 'reference_id'
        """)
        has_reference_id = cursor.fetchone()[0] > 0
        
        # Check if reference_type column exists
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.columns 
            WHERE table_name = 'transactions' 
            AND column_name = 'reference_type'
        """)
        has_reference_type = cursor.fetchone()[0] > 0
        
        # Add transaction_type column if it doesn't exist
        if not has_transaction_type:
            cursor.execute("ALTER TABLE transactions ADD COLUMN transaction_type ENUM('credit', 'debit') NOT NULL DEFAULT 'credit'")
            print("Added transaction_type column to transactions table")
        
        # Add reference_id column if it doesn't exist
        if not has_reference_id:
            cursor.execute("ALTER TABLE transactions ADD COLUMN reference_id INT")
            print("Added reference_id column to transactions table")
        
        # Add reference_type column if it doesn't exist
        if not has_reference_type:
            cursor.execute("ALTER TABLE transactions ADD COLUMN reference_type VARCHAR(50)")
            print("Added reference_type column to transactions table")
        
        # Check for created_at column
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.columns 
            WHERE table_name = 'transactions' 
            AND column_name = 'created_at'
        """)
        has_created_at = cursor.fetchone()[0] > 0
        
        # Add created_at column if it doesn't exist
        if not has_created_at:
            cursor.execute("ALTER TABLE transactions ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            print("Added created_at column to transactions table")
        
        conn.commit()
    except Exception as e:
        print(f"Error updating transactions table: {e}")
    finally:
        cursor.close()
        conn.close()

# Update the bills table to include quantity if it doesn't already exist
def update_bills_table():
    conn = connect_db()
    cursor = conn.cursor()
    try:
        # Check if quantity column exists
        cursor.execute("SHOW COLUMNS FROM bills LIKE 'quantity'")
        quantity_exists = cursor.fetchone()
        
        if not quantity_exists:
            cursor.execute("ALTER TABLE bills ADD COLUMN quantity INT DEFAULT 1 AFTER basic_amount")
            conn.commit()
            print("Added quantity column to bills table")
            
        # Check GST-related columns
        cursor.execute("SHOW COLUMNS FROM bills LIKE 'gst_type'")
        gst_type_exists = cursor.fetchone()
        
        if not gst_type_exists:
            cursor.execute("ALTER TABLE bills ADD COLUMN gst_type VARCHAR(20) DEFAULT NULL AFTER quantity")
            conn.commit()
            print("Added gst_type column to bills table")
            
        cursor.execute("SHOW COLUMNS FROM bills LIKE 'gst_percentage'")
        gst_percentage_exists = cursor.fetchone()
        
        if not gst_percentage_exists:
            cursor.execute("ALTER TABLE bills ADD COLUMN gst_percentage DECIMAL(5,2) DEFAULT 0 AFTER gst_type")
            conn.commit()
            print("Added gst_percentage column to bills table")
            
        cursor.execute("SHOW COLUMNS FROM bills LIKE 'gst_amount'")
        gst_amount_exists = cursor.fetchone()
        
        if not gst_amount_exists:
            cursor.execute("ALTER TABLE bills ADD COLUMN gst_amount DECIMAL(10,2) DEFAULT 0 AFTER gst_percentage")
            conn.commit()
            print("Added gst_amount column to bills table")
            
        cursor.execute("SHOW COLUMNS FROM bills LIKE 'total_amount'")
        total_amount_exists = cursor.fetchone()
        
        if not total_amount_exists:
            cursor.execute("ALTER TABLE bills ADD COLUMN total_amount DECIMAL(10,2) DEFAULT 0 AFTER gst_amount")
            conn.commit()
            print("Added total_amount column to bills table")
            
        # Update total_amount for any records that have it null but have basic_amount set
        cursor.execute("""
            UPDATE bills 
            SET total_amount = basic_amount + COALESCE(gst_amount, 0)
            WHERE (total_amount IS NULL OR total_amount = 0) AND basic_amount > 0
        """)
        conn.commit()
        print("Updated total_amount values where necessary")
            
    except Exception as e:
        print(f"Error updating bills table: {e}")
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
        # Start transaction
        conn.autocommit = False
        
        # Delete the transaction associated with this purchase first
        cursor.execute("DELETE FROM transactions WHERE reference_id = %s AND reference_type = 'billed_purchase'", (purchase_id,))
        
        # Now delete the purchase
        cursor.execute("DELETE FROM billed_purchases WHERE id = %s", (purchase_id,))
        
        # Commit the transaction
        conn.commit()
        flash("Purchase deleted successfully!", "success")
    except Exception as e:
        # Rollback on error
        conn.rollback()
        flash(f"Error deleting purchase: {str(e)}", "error")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('sales.billed_purchase'))

# Delete non-billed purchase
@sales.route('/delete_non_billed_purchase/<int:purchase_id>', methods=['GET'])
@login_required
def delete_non_billed_purchase(purchase_id):
    conn = connect_db()
    cursor = conn.cursor()
    try:
        # Start transaction
        conn.autocommit = False
        
        # Delete the transaction associated with this purchase first
        cursor.execute("DELETE FROM transactions WHERE reference_id = %s AND reference_type = 'purchase'", (purchase_id,))
        
        # Now delete the purchase
        cursor.execute("DELETE FROM purchases WHERE id = %s", (purchase_id,))
        
        # Commit the transaction
        conn.commit()
        flash("Purchase deleted successfully!", "success")
    except Exception as e:
        # Rollback on error
        conn.rollback()
        flash(f"Error deleting purchase: {str(e)}", "error")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('sales.non_billed_purchase'))

# Update sales tables to include payment_type
def update_sales_tables():
    conn = connect_db()
    cursor = conn.cursor()
    try:
        # Check if payment_type column exists in non_billed_sales
        cursor.execute("SHOW COLUMNS FROM non_billed_sales LIKE 'payment_type'")
        payment_type_exists = cursor.fetchone()
        
        # If the column doesn't exist, add it
        if not payment_type_exists:
            cursor.execute("ALTER TABLE non_billed_sales ADD COLUMN payment_type ENUM('Cash', 'Credit') DEFAULT 'Cash' AFTER amount")
            conn.commit()
            print("Added payment_type column to non_billed_sales table")
        # If the column exists but has incorrect type or default, modify it
        else:
            cursor.execute("ALTER TABLE non_billed_sales MODIFY COLUMN payment_type ENUM('Cash', 'Credit') DEFAULT 'Cash'")
            conn.commit()
            print("Updated payment_type column in non_billed_sales table")
        
        # Check if payment_type column exists in bills
        cursor.execute("SHOW COLUMNS FROM bills LIKE 'payment_type'")
        payment_type_exists = cursor.fetchone()
        
        # If the column doesn't exist, add it
        if not payment_type_exists:
            cursor.execute("ALTER TABLE bills ADD COLUMN payment_type ENUM('Cash', 'Credit') DEFAULT 'Cash' AFTER basic_amount")
            conn.commit()
            print("Added payment_type column to bills table")
        # If the column exists but has incorrect type or default, modify it
        else:
            cursor.execute("ALTER TABLE bills MODIFY COLUMN payment_type ENUM('Cash', 'Credit') DEFAULT 'Cash'")
            conn.commit()
            print("Updated payment_type column in bills table")
            
        # Similarly check and add/update payment_status columns
        cursor.execute("SHOW COLUMNS FROM non_billed_sales LIKE 'payment_status'")
        payment_status_exists = cursor.fetchone()
        
        if not payment_status_exists:
            cursor.execute("ALTER TABLE non_billed_sales ADD COLUMN payment_status ENUM('Pending', 'Paid') DEFAULT 'Paid' AFTER payment_type")
            conn.commit()
            print("Added payment_status column to non_billed_sales table")
        else:
            cursor.execute("ALTER TABLE non_billed_sales MODIFY COLUMN payment_status ENUM('Pending', 'Paid') DEFAULT 'Paid'")
            conn.commit()
            print("Updated payment_status column in non_billed_sales table")
            
        cursor.execute("SHOW COLUMNS FROM bills LIKE 'payment_status'")
        payment_status_exists = cursor.fetchone()
        
        if not payment_status_exists:
            cursor.execute("ALTER TABLE bills ADD COLUMN payment_status ENUM('Pending', 'Paid') DEFAULT 'Paid' AFTER payment_type")
            conn.commit()
            print("Added payment_status column to bills table")
        else:
            cursor.execute("ALTER TABLE bills MODIFY COLUMN payment_status ENUM('Pending', 'Paid') DEFAULT 'Paid'")
            conn.commit()
            print("Updated payment_status column in bills table")
            
    except Exception as e:
        print(f"Error updating sales tables: {e}")
    finally:
        cursor.close()
        conn.close()

# Credit Sales Route
@sales.route('/credit', methods=['GET'])
@login_required
def credit_sales():
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    credit_sales = []
    
    try:
        # Get credit sales from both tables
        cursor.execute("""
            SELECT 
                'bill' as sale_type, 
                id, 
                customer_name, 
                COALESCE(total_amount, basic_amount) as amount, 
                date, 
                payment_status 
            FROM bills 
            WHERE payment_type = 'Credit'
            
            UNION
            
            SELECT 
                'non_billed' as sale_type, 
                id, 
                customer_name, 
                amount, 
                date, 
                payment_status 
            FROM non_billed_sales 
            WHERE payment_type = 'Credit'
            
            ORDER BY date DESC
        """)
        credit_sales = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
    
    return render_template('credit_sales.html', credit_sales=credit_sales)

# Mark Credit Sale as Paid
@sales.route('/mark_as_paid/<string:sale_type>/<int:sale_id>', methods=['POST'])
@login_required
def mark_as_paid(sale_type, sale_id):
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        # Begin transaction
        conn.autocommit = False
        
        if sale_type == 'bill':
            cursor.execute("UPDATE bills SET payment_status = 'Paid', payment_type = 'Cash' WHERE id = %s", (sale_id,))
        elif sale_type == 'non_billed':
            cursor.execute("UPDATE non_billed_sales SET payment_status = 'Paid', payment_type = 'Cash' WHERE id = %s", (sale_id,))
        
        conn.commit()
        flash("Payment status updated successfully!", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error updating payment status: {str(e)}", "error")
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('sales.credit_sales'))

@sales.route('/test_db_structure', methods=['GET'])
@login_required
def test_db_structure():
    """A diagnostic route to check database structure"""
    conn = connect_db()
    cursor = conn.cursor()
    output = []
    
    try:
        # Check bills table structure
        cursor.execute("DESCRIBE bills")
        bills_columns = cursor.fetchall()
        output.append("Bills table structure:")
        for col in bills_columns:
            output.append(f"  {col[0]}: {col[1]}")
        
        # Check non_billed_sales table structure
        cursor.execute("DESCRIBE non_billed_sales")
        sales_columns = cursor.fetchall()
        output.append("\nNon-billed sales table structure:")
        for col in sales_columns:
            output.append(f"  {col[0]}: {col[1]}")
        
        # Check for recent sales with payment_type
        cursor.execute("SELECT id, customer_name, payment_type, payment_status, date FROM bills ORDER BY id DESC LIMIT 5")
        recent_bills = cursor.fetchall()
        output.append("\nRecent bills (with payment info):")
        for bill in recent_bills:
            output.append(f"  ID: {bill[0]}, Customer: {bill[1]}, Payment: {bill[2]}, Status: {bill[3]}, Date: {bill[4]}")
        
        cursor.execute("SELECT id, customer_name, payment_type, payment_status, date FROM non_billed_sales ORDER BY id DESC LIMIT 5")
        recent_sales = cursor.fetchall()
        output.append("\nRecent non-billed sales (with payment info):")
        for sale in recent_sales:
            output.append(f"  ID: {sale[0]}, Customer: {sale[1]}, Payment: {sale[2]}, Status: {sale[3]}, Date: {sale[4]}")
        
    except Exception as e:
        output.append(f"Error: {str(e)}")
    finally:
        cursor.close()
        conn.close()
    
    return "<pre>" + "\n".join(output) + "</pre>" 