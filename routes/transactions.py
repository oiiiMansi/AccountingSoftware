from flask import Blueprint, render_template, request, redirect, url_for
import mysql.connector

transactions = Blueprint('transactions', __name__)

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="roxanne",  
        database="accounting"
    )

@transactions.route('/transactions')
def show_transactions():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM transactions")
    transactions_data = cursor.fetchall()
    db.close()
    return render_template('transactions.html', transactions=transactions_data)

@transactions.route('/transactions/add', methods=['GET', 'POST'])
def add_transaction():
    if request.method == 'POST':
        description = request.form['description']
        amount = request.form['amount']
        date = request.form['date']
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("INSERT INTO transactions (description, amount, date) VALUES (%s, %s, %s)",
                       (description, amount, date))
        db.commit()
        db.close()
        return redirect(url_for('transactions.show_transactions'))
    return render_template('add_transaction.html')
