from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
import mysql.connector

leads = Blueprint('leads', __name__)

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="roxanne",
        database="accounting"
    )

# Show + Add Employee Target
@leads.route('/sales/leads', methods=['GET', 'POST'])
@login_required
def show_employee_targets():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        name = request.form.get('name')
        target_per_year = request.form.get('target_per_year')
        target_per_month = request.form.get('target_per_month')
        achieved_target_year = request.form.get('achieved_target_year')
        achieved_target_month = request.form.get('achieved_target_month')
        percentage_achieved = request.form.get('percentage_achieved')

        cursor.execute("""
            INSERT INTO employee_targets 
            (name, target_per_year, target_per_month, achieved_target_year, achieved_target_month, percentage_achieved)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (name, target_per_year, target_per_month, achieved_target_year, achieved_target_month, percentage_achieved))
        conn.commit()
        flash('Employee Target added successfully!', 'success')
        return redirect(url_for('leads.show_employee_targets'))

    cursor.execute("SELECT * FROM employee_targets ORDER BY created_at DESC")
    employees = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('leads.html', employees=employees)

# ✅ Delete Route
@leads.route('/sales/leads/delete/<int:id>', methods=['POST'])
@login_required
def delete_employee_target(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM employee_targets WHERE id = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Employee target deleted successfully!", "success")
    return redirect(url_for('leads.show_employee_targets'))

# ✅ Edit Route
@leads.route('/sales/leads/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_employee_target(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        name = request.form.get('name')
        target_per_year = request.form.get('target_per_year')
        target_per_month = request.form.get('target_per_month')
        achieved_target_year = request.form.get('achieved_target_year')
        achieved_target_month = request.form.get('achieved_target_month')
        percentage_achieved = request.form.get('percentage_achieved')

        cursor.execute("""
            UPDATE employee_targets 
            SET name=%s, target_per_year=%s, target_per_month=%s, 
                achieved_target_year=%s, achieved_target_month=%s, percentage_achieved=%s 
            WHERE id=%s
        """, (name, target_per_year, target_per_month, achieved_target_year, achieved_target_month, percentage_achieved, id))
        conn.commit()
        flash("Employee target updated successfully!", "success")
        return redirect(url_for('leads.show_employee_targets'))

    cursor.execute("SELECT * FROM employee_targets WHERE id = %s", (id,))
    employee = cursor.fetchone()

    cursor.close()
    conn.close()
    return render_template('edit_target.html', employee=employee)
