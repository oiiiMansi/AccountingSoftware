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
# from routes.budget import budget_bp  # Removed budget blueprint import
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
# app.register_blueprint(budget_bp)  # Removed budget blueprint registration
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

# Direct Purchase Route
@app.route("/purchase")
def direct_purchase():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Purchase Dashboard</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f4f4f4;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background-color: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
                text-align: center;
            }
            h1 {
                color: #333;
            }
            .options {
                display: flex;
                justify-content: center;
                gap: 20px;
                margin-top: 30px;
            }
            .card {
                background-color: #fff;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 20px;
                width: 200px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            .card h2 {
                margin-top: 0;
                color: #333;
            }
            .card p {
                color: #666;
                margin-bottom: 20px;
            }
            .btn {
                display: inline-block;
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                text-decoration: none;
                border-radius: 4px;
            }
            .back {
                display: inline-block;
                margin-top: 20px;
                color: #666;
                text-decoration: none;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Purchase Management</h1>
            
            <div class="options">
                <div class="card">
                    <h2>Billed Purchase</h2>
                    <p>Record purchases with GST</p>
                    <a href="/sales/billed_purchase" class="btn">Go to</a>
                </div>
                
                <div class="card">
                    <h2>Non-Billed Purchase</h2>
                    <p>Record purchases without GST</p>
                    <a href="/sales/non_billed_purchase" class="btn">Go to</a>
                </div>
            </div>
            
            <a href="/" class="back">← Back to Dashboard</a>
        </div>
    </body>
    </html>
    """

# Update the sales purchase route to use the same direct HTML
@app.route("/sales/purchase")
def sales_purchase():
    return redirect(url_for('direct_purchase'))

# Run the app
if __name__ == "__main__":
    app.run(debug=True)
