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
from routes.sales import sales  # Import the new sales blueprint

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
app.register_blueprint(sales, url_prefix='/sales')  # Register sales blueprint with prefix

# Home Route
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/accounting")
def accounting():
    return render_template("accounting.html")

@app.route('/sales/without_billing')
def without_billing():
    return render_template('without_billing.html')

# Revenue Route removed

# Run the app
if __name__ == "__main__":
    app.run(debug=True)
