from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
import mysql.connector
from flask_login import login_required
import pandas as pd
import io
from datetime import datetime

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

@transactions.route('/transactions/download')
@login_required
def download_transactions():
    try:
        # Connect to database
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Get all transactions
        cursor.execute("""
            SELECT 
                date, 
                description, 
                amount, 
                transaction_type,
                reference_type,
                reference_id,
                created_at 
            FROM transactions 
            ORDER BY date DESC
        """)
        transactions_data = cursor.fetchall()
        db.close()
        
        if not transactions_data:
            flash("No transactions to export", "error")
            return redirect(url_for('transactions.show_transactions'))
        
        # Create a DataFrame
        df = pd.DataFrame(transactions_data)
        
        # Format dates nicely
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
        if 'created_at' in df.columns:
            df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Calculate transaction source details
        def get_source(row):
            if pd.isna(row['reference_type']) or pd.isna(row['reference_id']):
                return 'Manual Entry'
            elif row['reference_type'] == 'purchase':
                return f"Purchase #{int(row['reference_id'])}"
            elif row['reference_type'] == 'billed_purchase':
                return f"Billed Purchase #{int(row['reference_id'])}"
            elif row['reference_type'] == 'non_billed_sale':
                return f"Non-billed Sale #{int(row['reference_id'])}"
            elif row['reference_type'] == 'bill':
                return f"Bill #{int(row['reference_id'])}"
            else:
                return f"{row['reference_type']} #{int(row['reference_id'])}"
        
        df['source'] = df.apply(get_source, axis=1)
        
        # Rename columns for better readability
        columns_to_display = {
            'date': 'Date',
            'description': 'Description',
            'amount': 'Amount',
            'transaction_type': 'Type',
            'source': 'Source',
            'created_at': 'Created At'
        }
        
        # Keep only necessary columns and rename them
        df = df[[col for col in columns_to_display.keys() if col in df.columns]]
        df = df.rename(columns={col: columns_to_display[col] for col in df.columns if col in columns_to_display})
        
        # Add summary rows
        # Calculate totals
        credit_total = df[df['Type'] == 'credit']['Amount'].sum() if 'Type' in df.columns else 0
        debit_total = df[df['Type'] == 'debit']['Amount'].sum() if 'Type' in df.columns else 0
        balance = credit_total - debit_total
        
        # Create summary DataFrame
        summary_df = pd.DataFrame({
            'Description': ['', 'TOTAL CREDIT (INCOME)', 'TOTAL DEBIT (EXPENSE)', 'BALANCE'],
            'Amount': ['', credit_total, debit_total, balance]
        })
        
        # Create Excel file in memory
        output = io.BytesIO()
        
        # Use openpyxl engine
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Transactions', index=False)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
        # Seek to the beginning of the stream
        output.seek(0)
        
        # Generate filename with current timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"transactions_{timestamp}.xlsx"
        
        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    
    except Exception as e:
        flash(f"Error generating Excel file: {str(e)}", "error")
        print(f"Excel generation error: {str(e)}")
        return redirect(url_for('transactions.show_transactions'))
