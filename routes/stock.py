from flask import Blueprint, render_template, request, redirect, url_for, flash
import mysql.connector
from flask_login import login_required

stock = Blueprint('stock', __name__)

def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="roxanne",
        database="accounting"
    )

@stock.route('/stock', methods=['GET', 'POST'])
@login_required
def stock_page():
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)

    try:
        if request.method == 'POST':
            item_name = request.form['item_name']
            quantity = request.form['quantity']

            cursor.execute("INSERT INTO stock (item_name, quantity) VALUES (%s, %s)", 
                           (item_name, quantity))
            conn.commit()
            flash("Stock added successfully!", "success")
            return redirect(url_for('stock.stock_page'))

        cursor.execute("SELECT * FROM stock ORDER BY added_at DESC")
        stock_items = cursor.fetchall()

    finally:
        cursor.close()
        conn.close()

    return render_template('stock.html', stock=stock_items)
