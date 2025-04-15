from flask import Blueprint, render_template, request, redirect, url_for, flash
import mysql.connector
from flask_login import login_required

stock = Blueprint('stock', __name__)

# Database connection
def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="roxanne",
        database="accounting"
    )

# View and Add Stock
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

        cursor.execute("SELECT * FROM stock ORDER BY id DESC")
        stock_items = cursor.fetchall()

    finally:
        cursor.close()
        conn.close()

    return render_template('stock.html', stock=stock_items)

# Edit Stock Item
@stock.route('/stock/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_stock(id):
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)

    try:
        if request.method == 'POST':
            item_name = request.form['item_name']
            quantity = request.form['quantity']

            cursor.execute(
                "UPDATE stock SET item_name = %s, quantity = %s WHERE id = %s",
                (item_name, quantity, id)
            )
            conn.commit()
            flash("Stock updated successfully!", "success")
            return redirect(url_for('stock.stock_page'))

        cursor.execute("SELECT * FROM stock WHERE id = %s", (id,))
        stock_item = cursor.fetchone()

        if not stock_item:
            flash("Stock item not found.", "danger")
            return redirect(url_for('stock.stock_page'))

    finally:
        cursor.close()
        conn.close()

    return render_template('edit_stock.html', stock_item=stock_item)

# Delete Stock Item
@stock.route('/stock/delete/<int:id>', methods=['POST'])
@login_required
def delete_stock(id):
    conn = connect_db()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM stock WHERE id = %s", (id,))
        conn.commit()
        flash("Stock deleted successfully!", "success")

    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('stock.stock_page'))
