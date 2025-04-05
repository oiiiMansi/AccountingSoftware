from flask import Flask, render_template
from flask_login import LoginManager
import mysql.connector
from models import User, load_user  
from routes.auth import auth
from routes.billing import billing
from routes.expenses import expenses
from routes.stock import stock

# Initialize Flask app
app = Flask(__name__)
app.secret_key = "your_secret_key"  # Replace with secure key in production

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"  # Redirect to login view if not authenticated

# Register the user loader function for Flask-Login

from models import load_user  

login_manager.user_loader(load_user)  
# Register Blueprints
app.register_blueprint(auth)
app.register_blueprint(billing)
app.register_blueprint(expenses)
app.register_blueprint(stock)

# Home Page Route
@app.route("/")
def home():
    return render_template("index.html")

# Additional Routes (Accounting, Invoicing, etc.)
@app.route('/accounting')
def accounting():
    return render_template('accounting.html')

@app.route('/invoicing')
def invoicing():
    return render_template('invoicing.html')

@app.route('/budgeting')
def budgeting():
    return render_template('budgeting.html')

if __name__ == "__main__":
    app.run(debug=True)
