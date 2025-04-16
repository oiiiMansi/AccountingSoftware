from flask import Blueprint, render_template, request, redirect, url_for, flash
import mysql.connector
from flask_login import login_required

transactions = Blueprint('transactions', __name__)

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="roxanne",  
        database="accounting"
    )

def create_transactions_table():
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            date DATE NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            description VARCHAR(255) NOT NULL,
            transaction_type ENUM('credit', 'debit') NOT NULL DEFAULT 'credit',
            reference_id INT,
            reference_type VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        db.commit()
        cursor.close()
        db.close()
    except Exception as e:
        print(f"Error creating transactions table: {e}")

def update_transactions_table():
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        # Check if transaction_type column exists
        cursor.execute("""
            SELECT COUNT(*) as count FROM information_schema.columns 
            WHERE table_name = 'transactions' 
            AND column_name = 'transaction_type'
        """)
        has_transaction_type = cursor.fetchone()[0] > 0
        
        # Check if reference_id column exists
        cursor.execute("""
            SELECT COUNT(*) as count FROM information_schema.columns 
            WHERE table_name = 'transactions' 
            AND column_name = 'reference_id'
        """)
        has_reference_id = cursor.fetchone()[0] > 0
        
        # Check if reference_type column exists
        cursor.execute("""
            SELECT COUNT(*) as count FROM information_schema.columns 
            WHERE table_name = 'transactions' 
            AND column_name = 'reference_type'
        """)
        has_reference_type = cursor.fetchone()[0] > 0
        
        # Add transaction_type column if it doesn't exist
        if not has_transaction_type:
            cursor.execute("ALTER TABLE transactions ADD COLUMN transaction_type ENUM('credit', 'debit') NOT NULL DEFAULT 'credit'")
        
        # Add reference_id column if it doesn't exist
        if not has_reference_id:
            cursor.execute("ALTER TABLE transactions ADD COLUMN reference_id INT")
        
        # Add reference_type column if it doesn't exist
        if not has_reference_type:
            cursor.execute("ALTER TABLE transactions ADD COLUMN reference_type VARCHAR(50)")
        
        # Add created_at column if it doesn't exist
        cursor.execute("""
            SELECT COUNT(*) as count FROM information_schema.columns 
            WHERE table_name = 'transactions' 
            AND column_name = 'created_at'
        """)
        has_created_at = cursor.fetchone()[0] > 0
        
        if not has_created_at:
            cursor.execute("ALTER TABLE transactions ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        
        db.commit()
        print("Transactions table updated successfully")
    except Exception as e:
        print(f"Error updating transactions table: {e}")
    finally:
        cursor.close()
        db.close()

@transactions.route('/transactions')
@login_required
def show_transactions():
    update_transactions_table()  # Update table structure if needed
    
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM transactions ORDER BY date DESC")
        transactions_data = cursor.fetchall()
        db.close()
        return render_template('transactions.html', transactions=transactions_data)
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        print(f"Error: {e}")
        return render_template('transactions.html', transactions=[])

@transactions.route('/transactions/add', methods=['GET', 'POST'])
@login_required
def add_transaction():
    if request.method == 'POST':
        description = request.form['description']
        amount = request.form['amount']
        date = request.form['date']
        transaction_type = request.form.get('transaction_type', 'credit')
        
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("INSERT INTO transactions (description, amount, date, transaction_type) VALUES (%s, %s, %s, %s)",
                      (description, amount, date, transaction_type))
        db.commit()
        db.close()
        flash("Transaction added successfully!", "success")
        return redirect(url_for('transactions.show_transactions'))
    return render_template('add_transaction.html')

@transactions.route('/transactions/delete/<int:id>', methods=['POST', 'GET'])
@login_required
def delete_transaction(id):
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("DELETE FROM transactions WHERE id = %s", (id,))
        db.commit()
        db.close()
        flash("Transaction deleted successfully!", "success")
    except Exception as e:
        flash(f"Error deleting transaction: {e}", "error")
    
    return redirect(url_for('transactions.show_transactions'))
