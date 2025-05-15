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
    return render_template("purchase_dashboard.html")

# Update the sales purchase route to use the same direct HTML
@app.route("/sales/purchase")
@login_required
def sales_purchase():
    return redirect(url_for('direct_purchase'))

# Sales Dashboard Route
@app.route("/sales")
@login_required
def sales_dashboard():
    return render_template("sales_dashboard.html")

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
