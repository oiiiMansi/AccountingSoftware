from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_required, current_user
import mysql.connector

# Models
from models import User, load_user

# Blueprints
from routes.auth import auth
from routes.billing import billing
from routes.expenses import expenses
from routes.stock import stock
from routes.leads import leads  
from routes.reports import reports
from routes.transactions import transactions
from routes.salary import salary
from routes.employees import employees
from routes.sales import sales, update_sales_tables, update_purchase_tables  

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
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "warning"
login_manager.user_loader(load_user)

# Context processor to make current_user available in all templates
@app.context_processor
def inject_user():
    return dict(current_user=current_user)

# Register Blueprints
app.register_blueprint(auth)
app.register_blueprint(billing, url_prefix='')
app.register_blueprint(expenses)
app.register_blueprint(stock)
app.register_blueprint(leads)  
app.register_blueprint(reports)
app.register_blueprint(transactions)
app.register_blueprint(salary)
app.register_blueprint(employees)
app.register_blueprint(sales, url_prefix='/sales')

# Update database tables for partial payment support
with app.app_context():
    update_sales_tables()
    update_purchase_tables()

# Redirect old reports URL to new one
@app.route("/reports")
def redirect_reports():
    return redirect(url_for('reports.show_reports'))

# Home Route
@app.route("/")
@login_required
def home():
    return render_template("index.html")

@app.route("/accounting")
@login_required
def accounting():
    return render_template("accounting.html")

@app.route('/sales/without_billing')
@login_required
def without_billing_page():
    # Check if the route exists in the sales blueprint
    try:
        return redirect(url_for('sales.without_billing'))
    except:
        # If not, forward to your actual without billing implementation
        return render_template('without_billing.html')

# Revenue Route removed

# Direct Purchase Route
@app.route("/purchase")
@login_required
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
                
                <div class="card">
                    <h2>Credit Purchases</h2>
                    <p>Manage pending credits</p>
                    <a href="/sales/credit_purchases" class="btn">Go to</a>
                </div>
            </div>
            
            <a href="/" class="back">← Back to Dashboard</a>
        </div>
    </body>
    </html>
    """

# Update the sales purchase route to use the same direct HTML
@app.route("/sales/purchase")
@login_required
def sales_purchase():
    return redirect(url_for('direct_purchase'))

# Sales Dashboard Route
@app.route("/sales")
@login_required
def sales_dashboard():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sales Dashboard</title>
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
                flex-wrap: wrap;
            }
            .card {
                background-color: #fff;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 20px;
                width: 200px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                margin-bottom: 15px;
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
            <h1>Sales Management</h1>
            
            <div class="options">
                <div class="card">
                    <h2>Billing</h2>
                    <p>Create invoices with GST</p>
                    <a href="/billing" class="btn">Go to</a>
                </div>
                
                <div class="card">
                    <h2>Without Billing</h2>
                    <p>Record sales without invoices</p>
                    <a href="/sales/without_billing" class="btn">Go to</a>
                </div>
                
                <div class="card">
                    <h2>Credit Sales</h2>
                    <p>Manage pending credit sales</p>
                    <a href="/sales/credit" class="btn">Go to</a>
                </div>
            </div>
            
            <a href="/" class="back">← Back to Dashboard</a>
        </div>
    </body>
    </html>
    """

# Update the sales route to use the same direct HTML
@app.route("/sales/dashboard")
def sales_route_dashboard():
    return redirect(url_for('sales_dashboard'))

# Redirect old URLs to new structure
@app.route('/sales/billing')
def redirect_sales_billing():
    return redirect(url_for('billing.billing_page'))

# Run the app
if __name__ == "__main__":
    app.run(debug=True)
