from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager
import mysql.connector

# Models
from models import User, load_user

# Blueprints
from routes.auth import auth
from routes.billing import billing
from routes.expenses import expenses
from routes.stock import stock
from routes.budget import budget_bp
from routes.leads import leads  # Ab yeh Employee Target handle karega
from routes.reports import reports
from routes.transactions import transactions
from routes.salary import salary
from routes.employees import employees

# Flask App
app = Flask(__name__)
app.secret_key = "your_secret_key"

# MySQL DB connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="roxanne",
    database="accounting"
)

# Make DB available in Blueprints too
app.db = db

# Flask-Login Setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"
login_manager.user_loader(load_user)

# Register Blueprints
app.register_blueprint(auth)
app.register_blueprint(billing)
app.register_blueprint(expenses)
app.register_blueprint(stock)
app.register_blueprint(budget_bp)
app.register_blueprint(leads)  # employee target handled here
app.register_blueprint(reports)
app.register_blueprint(transactions)
app.register_blueprint(salary)
app.register_blueprint(employees)

# Home Route
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/accounting")
def accounting():
    return render_template("accounting.html")

@app.route("/invoicing")
def invoicing():
    return render_template("invoicing.html")

# Revenue Route
@app.route('/revenue', methods=['GET', 'POST'])
def revenue():
    cursor = db.cursor(dictionary=True)
    if request.method == "POST":
        source = request.form["source"]
        amount = request.form["amount"]
        date = request.form["date"]
        cursor.execute(
            "INSERT INTO revenue (source, amount, date) VALUES (%s, %s, %s)",
            (source, amount, date)
        )
        db.commit()
        return redirect(url_for("revenue"))

    cursor.execute("SELECT * FROM revenue ORDER BY date DESC")
    records = cursor.fetchall()
    return render_template("revenue.html", revenues=records)

# Run the app
if __name__ == "__main__":
    app.run(debug=True)
