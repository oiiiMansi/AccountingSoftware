from flask import Blueprint, render_template, request, redirect, url_for, send_file
import mysql.connector
from fpdf import FPDF
import os

salary = Blueprint("salary", __name__)
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="roxanne", 
    database="accounting"
)

@salary.route("/salary", methods=["GET", "POST"])
def salary_page():
    cursor = db.cursor(dictionary=True)
    
    if request.method == "POST":
        try:
            name = request.form["name"]
            amount = request.form["amount"]
            date = request.form["date"]
        except KeyError as e:
            return f"Missing form field: {e}", 400

        cursor.execute(
            "INSERT INTO salary (employee_name, amount, date) VALUES (%s, %s, %s)",
            (name, amount, date)
        )
        db.commit()
        return redirect(url_for("salary.salary_page"))

    cursor.execute("SELECT id, employee_name, amount, date FROM salary ORDER BY date DESC")
    salaries = cursor.fetchall()
    return render_template("salary.html", salaries=salaries)

@salary.route("/download-slip/<int:salary_id>")
def download_slip(salary_id):
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM salary WHERE id = %s", (salary_id,))
    record = cursor.fetchone()

    if not record:
        return "Salary record not found.", 404

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    pdf.cell(200, 10, txt="Salary Slip - KK Enterprises", ln=True, align='C')
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Employee: {record['employee_name']}", ln=True)
    pdf.cell(200, 10, txt=f"Amount: Rs. {record['amount']}", ln=True)
    pdf.cell(200, 10, txt=f"Date: {record['date']}", ln=True)

    pdf_path = f"salary_slip_{salary_id}.pdf"
    pdf.output(pdf_path)

    return send_file(pdf_path, as_attachment=True)
