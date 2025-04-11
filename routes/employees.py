from flask import Blueprint, render_template, request, redirect, url_for
import mysql.connector

employees = Blueprint('employees', __name__)

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="roxanne",
    database="accounting"
)

@employees.route("/employees")
def employees_page():
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM employees ORDER BY id DESC")
    records = cursor.fetchall()
    return render_template("employees.html", employees=records)

@employees.route("/employees/add", methods=["POST"])
def add_employee():
    full_name = request.form.get("full_name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    dob = request.form.get("dob")
    gender = request.form.get("gender")
    department = request.form.get("department")
    position = request.form.get("position")
    joining_date = request.form.get("joining_date")
    salary = request.form.get("salary")
    address = request.form.get("address")

    if not full_name or not email:
        return "Missing required fields", 400

    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO employees 
        (full_name, email, phone, dob, gender, department, position, joining_date, salary, address)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (full_name, email, phone, dob, gender, department, position, joining_date, salary, address))

    db.commit()
    return redirect(url_for("employees.employees_page"))




@employees.route("/employees/edit/<int:id>", methods=["GET", "POST"])
def edit_employee(id):
    cursor = db.cursor(dictionary=True)
    if request.method == "POST":
        full_name = request.form.get("full_name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        dob = request.form.get("dob")
        gender = request.form.get("gender")
        department = request.form.get("department")
        position = request.form.get("position")
        joining_date = request.form.get("joining_date")
        salary = request.form.get("salary")
        address = request.form.get("address")

        
        print("DEBUG:", full_name, email)  # ← ADD THIS

        cursor.execute("""
            UPDATE employees SET 
            full_name=%s, email=%s, phone=%s, dob=%s, gender=%s, 
            department=%s, position=%s, joining_date=%s, salary=%s, address=%s 
            WHERE id=%s
        """, (full_name, email, phone, dob, gender, department, position, joining_date, salary, address, id))

        db.commit()
        return redirect(url_for("employees.employees_page"))
    else:
        cursor.execute("SELECT * FROM employees WHERE id = %s", (id,))
        employee = cursor.fetchone()
        return render_template("edit_employee.html", employee=employee)

@employees.route("/employees/delete/<int:id>")
def delete_employee(id):
    cursor = db.cursor()
    cursor.execute("DELETE FROM employees WHERE id = %s", (id,))
    db.commit()
    return redirect(url_for("employees.employees_page"))
