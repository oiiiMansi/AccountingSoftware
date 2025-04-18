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

def create_bills_table():
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS bills (
            id INT AUTO_INCREMENT PRIMARY KEY,
            customer_name VARCHAR(255) NOT NULL,
            customer_number VARCHAR(50),
            customer_address TEXT,
            shipping_address TEXT,
            date DATE NOT NULL,
            basic_amount DECIMAL(10,2) NOT NULL,
            gst_type VARCHAR(20) DEFAULT 'CGST_SGST',
            gst_percentage DECIMAL(5,2) DEFAULT 18.00,
            gst_amount DECIMAL(10,2),
            total_amount DECIMAL(10,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.commit()
    except Exception as e:
        print(f"Error creating bills table: {e}")
    finally:
        cursor.close()
        conn.close()

# Billing Route (GET and POST)
@billing.route('/billing', methods=['GET', 'POST'])
@login_required
def billing_page():
    # Ensure the table exists
    create_bills_table()
    
    # Update transactions table if needed
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        # Check if transaction_type column exists
        cursor.execute("""
            SELECT COUNT(*) as count FROM information_schema.columns 
            WHERE table_name = 'transactions' 
            AND column_name = 'transaction_type'
        """)
        has_transaction_type = cursor.fetchone()[0] > 0
        
        # Check if reference columns exist
        cursor.execute("""
            SELECT COUNT(*) as count FROM information_schema.columns 
            WHERE table_name = 'transactions' 
            AND column_name = 'reference_id'
        """)
        has_reference_id = cursor.fetchone()[0] > 0
        
        cursor.execute("""
            SELECT COUNT(*) as count FROM information_schema.columns 
            WHERE table_name = 'transactions' 
            AND column_name = 'reference_type'
        """)
        has_reference_type = cursor.fetchone()[0] > 0
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error checking transactions table: {e}")
        has_transaction_type = False
        has_reference_id = False
        has_reference_type = False
    
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)

    try:
        if request.method == 'POST':
            # Get form data
            customer_name = request.form['customer_name']
            customer_number = request.form.get('customer_number', '')
            customer_address = request.form.get('customer_address', '')
            shipping_address = request.form.get('shipping_address', '')
            date = request.form['date']
            basic_amount = Decimal(request.form['basic_amount'])
            gst_type = request.form.get('gst_type', 'CGST_SGST')
            gst_percentage = Decimal(request.form.get('gst_percentage', 18.0))

            # Calculate GST and total amount
            gst_amount = (basic_amount * gst_percentage) / 100
            total_amount = basic_amount + gst_amount

            # Start transaction
            conn.autocommit = False
            
            try:
                # Insert the bill into the database
                cursor.execute(
                    """INSERT INTO bills 
                       (customer_name, customer_number, customer_address, shipping_address, 
                        date, basic_amount, gst_type, gst_percentage, gst_amount, total_amount) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (customer_name, customer_number, customer_address, shipping_address, 
                     date, basic_amount, gst_type, gst_percentage, gst_amount, total_amount)
                )
                
                # Get the ID of the inserted bill
                bill_id = cursor.lastrowid
                
                # Add to transactions if necessary columns exist
                if has_transaction_type and has_reference_id and has_reference_type:
                    description = f"Bill to {customer_name}"
                    cursor.execute(
                        """INSERT INTO transactions 
                           (description, amount, date, transaction_type, reference_id, reference_type) 
                           VALUES (%s, %s, %s, 'credit', %s, 'bill')""",
                        (description, total_amount, date, bill_id)
                    )
                else:
                    # Just add a basic transaction
                    description = f"Bill to {customer_name}"
                    cursor.execute(
                        "INSERT INTO transactions (description, amount, date) VALUES (%s, %s, %s)",
                        (description, total_amount, date)
                    )
                
                # Commit both operations
                conn.commit()
                flash("Invoice added successfully!", "success")
            except Exception as e:
                # Rollback on error
                conn.rollback()
                flash(f"Error: {str(e)}", "error")
                print(f"Database error: {str(e)}")
            finally:
                # Reset autocommit
                conn.autocommit = True

            return redirect(url_for('billing.billing_page'))

        # Fetch all billing entries
        cursor.execute("SELECT * FROM bills ORDER BY date DESC")
        bills_list = cursor.fetchall()
        
        # For debugging
        print(f"Found {len(bills_list)} bills")
        if bills_list:
            print(f"First bill: {bills_list[0]}")

    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        print(f"Database error: {str(e)}")
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
    
    # Start transaction
    conn.autocommit = False
    
    try:
        # Delete the bill
        cursor.execute("DELETE FROM bills WHERE id = %s", (bill_id,))
        
        # Check if reference_id column exists in transactions table
        cursor.execute("""
            SELECT COUNT(*) as count FROM information_schema.columns 
            WHERE table_name = 'transactions' 
            AND column_name = 'reference_id'
        """)
        has_reference_id = cursor.fetchone()[0] > 0
        
        # Only try to delete related transactions if the reference columns exist
        if has_reference_id:
            cursor.execute("""
                SELECT COUNT(*) as count FROM information_schema.columns 
                WHERE table_name = 'transactions' 
                AND column_name = 'reference_type'
            """)
            has_reference_type = cursor.fetchone()[0] > 0
            
            if has_reference_type:
                # Delete associated transaction
                cursor.execute("DELETE FROM transactions WHERE reference_id = %s AND reference_type = 'bill'", (bill_id,))
        
        # Commit operations
        conn.commit()
        flash("Invoice deleted successfully!", "success")
    except Exception as e:
        # Rollback on error
        conn.rollback()
        flash(f"Error: {str(e)}", "error")
    finally:
        # Reset autocommit
        conn.autocommit = True
        cursor.close()
        conn.close()

    return redirect(url_for('billing.billing_page'))

# Edit a bill
@billing.route('/billing/edit/<int:bill_id>', methods=['GET', 'POST'])
@login_required
def edit_bill(bill_id):
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    bill = None  # Initialize with a default value
    
    try:
        if request.method == 'POST':
            # Get form data
            customer_name = request.form['customer_name']
            customer_number = request.form.get('customer_number', '')
            customer_address = request.form.get('customer_address', '')
            shipping_address = request.form.get('shipping_address', '')
            date = request.form['date']
            basic_amount = Decimal(request.form['basic_amount'])
            gst_type = request.form.get('gst_type', 'CGST_SGST')
            gst_percentage = Decimal(request.form.get('gst_percentage', 18.0))

            # Calculate GST and total amount
            gst_amount = (basic_amount * gst_percentage) / 100
            total_amount = basic_amount + gst_amount

            # Start transaction
            conn.autocommit = False
            
            try:
                # Update the bill
                cursor.execute("""
                    UPDATE bills SET
                        customer_name = %s,
                        customer_number = %s,
                        customer_address = %s,
                        shipping_address = %s,
                        date = %s,
                        basic_amount = %s,
                        gst_type = %s,
                        gst_percentage = %s,
                        gst_amount = %s,
                        total_amount = %s
                    WHERE id = %s
                """, (
                    customer_name, customer_number, customer_address, shipping_address,
                    date, basic_amount, gst_type, gst_percentage, gst_amount, total_amount,
                    bill_id
                ))
                
                # Check if transaction table has the appropriate columns
                cursor.execute("""
                    SELECT COUNT(*) as count FROM information_schema.columns 
                    WHERE table_name = 'transactions' 
                    AND column_name = 'reference_id'
                """)
                has_reference_id = cursor.fetchone()['count'] > 0
                
                if has_reference_id:
                    # Check for reference_type
                    cursor.execute("""
                        SELECT COUNT(*) as count FROM information_schema.columns 
                        WHERE table_name = 'transactions' 
                        AND column_name = 'reference_type'
                    """)
                    has_reference_type = cursor.fetchone()['count'] > 0
                    
                    if has_reference_type:
                        # Update associated transaction
                        description = f"Bill to {customer_name}"
                        cursor.execute("""
                            UPDATE transactions SET
                                description = %s,
                                amount = %s,
                                date = %s
                            WHERE reference_id = %s AND reference_type = 'bill'
                        """, (description, total_amount, date, bill_id))
                
                # Commit both operations
                conn.commit()
                flash("Invoice updated successfully!", "success")
            except Exception as e:
                # Rollback on error
                conn.rollback()
                flash(f"Error: {str(e)}", "error")
            finally:
                # Reset autocommit
                conn.autocommit = True
                
            return redirect(url_for('billing.billing_page'))

        # For GET request, show existing bill details
        cursor.execute("SELECT * FROM bills WHERE id = %s", (bill_id,))
        bill = cursor.fetchone()
        
        if not bill:
            flash("Bill not found", "error")
            return redirect(url_for('billing.billing_page'))

    except Exception as e:
        flash(f"Error: {str(e)}", "error")
    finally:
        cursor.close()
        conn.close()

    # Check if bill is None before rendering the template
    if bill is None:
        flash("Bill not found", "error")
        return redirect(url_for('billing.billing_page'))
        
    return render_template('edit_bill.html', bill=bill)
