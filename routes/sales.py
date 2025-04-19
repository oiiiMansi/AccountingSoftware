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
    # Ensure table has quantity column
    update_bills_table()
    
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)

    try:
        if request.method == 'POST':
            # Get form data
            customer_name = request.form['customer_name']
            amount = Decimal(request.form['basic_amount'])
            quantity = int(request.form.get('quantity', 1))  # Default to 1 if not provided
            date = request.form['date']
            
            # Get other form fields if available
            customer_number = request.form.get('customer_number', '')
            customer_address = request.form.get('customer_address', '')
            shipping_address = request.form.get('shipping_address', '')
            gst_type = request.form.get('gst_type', '')
            gst_percentage = request.form.get('gst_percentage', '')

            # Insert the bill into the database with all available columns
            cursor.execute(
                """
                INSERT INTO bills 
                (customer_name, customer_number, customer_address, shipping_address, 
                basic_amount, quantity, gst_type, gst_percentage, date) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (customer_name, customer_number, customer_address, shipping_address, 
                amount, quantity, gst_type, gst_percentage, date)
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
    # Ensure tables exist with proper schema
    create_non_billed_sales_table()
    update_transactions_table()
    
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    sales_list = []
    
    try:
        if request.method == 'POST':
            # Get form data
            customer_name = request.form['customer_name']
            contact_number = request.form['contact_number']
            item_details = request.form['item_details']
            quantity = int(request.form.get('quantity', 1))  # Default to 1 if not provided
            amount = Decimal(request.form['amount'])
            date = request.form['date']
            notes = request.form.get('notes', '')

            # Start a transaction
            conn.autocommit = False
            
            try:
                # Insert into non_billed_sales table
                cursor.execute(
                    """
                    INSERT INTO non_billed_sales 
                    (customer_name, contact_number, item_details, quantity, amount, date, notes) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (customer_name, contact_number, item_details, quantity, amount, date, notes)
                )
                # Get the ID of the inserted sale
                sale_id = cursor.lastrowid
                
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
                flash("Sale recorded successfully!", "success")
            except Exception as e:
                # Rollback on error
                conn.rollback()
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
            quantity = int(request.form.get('quantity', 1))
            amount = Decimal(request.form['amount'])
            date = request.form['date']
            notes = request.form.get('notes', '')

            # Update the sale
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
            gst_percentage = request.form.get('gst_percentage', '')

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
                    date = %s
                WHERE id = %s
            """, (
                customer_name, customer_number, customer_address, shipping_address,
                basic_amount, quantity, gst_type, gst_percentage, date, bill_id
            ))
            conn.commit()
            flash("Bill updated successfully!", "success")
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
                    "INSERT INTO billed_purchases (vendor_name, amount, gst_type, gst_percentage, date, description) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                    (vendor_name, amount, gst_type, gst_percentage, date, description)
                )
                # Get the ID of the inserted purchase
                purchase_id = cursor.lastrowid
                
                # Add to transactions as debit
                transaction_description = f"Billed purchase from {vendor_name}: {description or 'No description'} (with GST)"
                
                cursor.execute(
                    """INSERT INTO transactions 
                       (description, amount, date, transaction_type, reference_id, reference_type) 
                       VALUES (%s, %s, %s, 'debit', %s, 'billed_purchase')""",
                    (transaction_description, total_amount, date, purchase_id)
                )
                
                # Commit both operations
                conn.commit()
                flash("Billed purchase recorded successfully and added to transactions!", "success")
            except Exception as e:
                # Rollback on error
                conn.rollback()
                flash(f"Error: {str(e)}", "error")
                print(f"Database error in billed_purchase: {str(e)}")
            finally:
                # Reset autocommit
                conn.autocommit = True
                
            return redirect(url_for('sales.billed_purchase'))
            
        # Fetch all billed purchases
        cursor.execute("SELECT * FROM billed_purchases ORDER BY date DESC")
        purchases_list = cursor.fetchall()
        
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        print(f"Error in billed_purchase route: {str(e)}")
    finally:
        cursor.close()
        conn.close()
        
    return render_template('billed_purchase.html', purchases=purchases_list)

# Non-Billed Purchase Route
@sales.route('/non_billed_purchase', methods=['GET', 'POST'])
@login_required
def non_billed_purchase():
    # Ensure tables exist with proper schema
    create_purchase_table()
    update_transactions_table()
    
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
            
            # Start transaction
            conn.autocommit = False
            
            try:
                # Insert purchase record
                cursor.execute(
                    "INSERT INTO purchases (vendor_name, amount, date, item_details, notes) VALUES (%s, %s, %s, %s, %s)",
                    (vendor_name, amount, date, item_details, notes)
                )
                # Get the ID of the inserted purchase
                purchase_id = cursor.lastrowid
                
                # Add to transactions as debit
                description = f"Purchase from {vendor_name}: {item_details}"
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
            finally:
                # Reset autocommit to default
                conn.autocommit = True
        
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
    
    # Start transaction
    conn.autocommit = False
    
    try:
        # Delete the purchase
        cursor.execute("DELETE FROM billed_purchases WHERE id = %s", (purchase_id,))
        
        # Delete associated transaction
        cursor.execute("DELETE FROM transactions WHERE reference_id = %s AND reference_type = 'billed_purchase'", (purchase_id,))
        
        # Commit both operations
        conn.commit()
        flash("Purchase and associated transaction deleted successfully!", "success")
    except Exception as e:
        # Rollback on error
        conn.rollback()
        flash(f"Error: {str(e)}", "error")
        print(f"Error deleting billed purchase: {str(e)}")
    finally:
        # Reset autocommit
        conn.autocommit = True
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
    
    # Start transaction
    conn.autocommit = False
    
    try:
        # Delete the purchase
        cursor.execute("DELETE FROM purchases WHERE id = %s", (purchase_id,))
        
        # Delete associated transaction
        cursor.execute("DELETE FROM transactions WHERE reference_id = %s AND reference_type = 'purchase'", (purchase_id,))
        
        # Commit both operations
        conn.commit()
        flash("Purchase and associated transaction deleted successfully!", "success")
    except Exception as e:
        # Rollback on error
        conn.rollback()
        flash(f"Error: {str(e)}", "error")
        print(f"Error deleting non-billed purchase: {str(e)}")
    finally:
        # Reset autocommit
        conn.autocommit = True
        cursor.close()
        conn.close()
        
    return redirect(url_for('sales.non_billed_purchase'))

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
    except Exception as e:
        print(f"Error updating bills table: {e}")
    finally:
        cursor.close()
        conn.close() 