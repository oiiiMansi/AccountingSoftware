from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
import mysql.connector

leads = Blueprint('leads', __name__)

# ✅ Database connection helper
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",         # ✅ Change to your DB user
        password="roxanne",         # ✅ Set your DB password
        database="accounting"     # ✅ Set your DB name
    )

# ✅ Show leads
@leads.route('/sales/leads', methods=['GET', 'POST'])
@login_required
def show_leads():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        name = request.form.get('name')
        contact = request.form.get('contact')
        company = request.form.get('company')
        source = request.form.get('source')
        status = request.form.get('status')
        assigned_to = request.form.get('assigned_to')

        cursor.execute("""
            INSERT INTO leads (name, contact, company, source, status, assigned_to)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (name, contact, company, source, status, assigned_to))
        conn.commit()
        flash('Lead added successfully!', 'success')
        return redirect(url_for('leads.show_leads'))

    cursor.execute("SELECT * FROM leads ORDER BY created_at DESC")
    leads_data = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('leads.html', leads=leads_data)
