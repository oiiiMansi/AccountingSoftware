from flask_login import UserMixin
import mysql.connector
from datetime import datetime, date

# Database connection function
def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="roxanne",
        database="accounting"
    )

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, role):
        self.id = id
        self.username = username
        self.role = role

    def is_admin(self):
        return self.role == 'admin'

    def is_accountant(self):
        return self.role == 'accountant'

    def is_viewer(self):
        return self.role == 'viewer'

    def has_role(self, role):
        return self.role == role

# User loader function for Flask-Login (Fixing RecursionError)
def load_user(user_id):
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if user:
        return User(user["id"], user["username"], user["role"])
    
    return None  # Prevents infinite recursion

# Tax Rate model
class TaxRate:
    def __init__(self, id=None, name=None, type=None, rate=None, description=None, 
                 is_active=True, hsn_code=None, effective_from=None, effective_to=None):
        self.id = id
        self.name = name
        self.type = type
        self.rate = rate
        self.description = description
        self.is_active = is_active
        self.hsn_code = hsn_code
        self.effective_from = effective_from
        self.effective_to = effective_to
    
    @staticmethod
    def get_all():
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM tax_rates ORDER BY type, rate")
        tax_rates = cursor.fetchall()
        cursor.close()
        conn.close()
        return tax_rates
    
    @staticmethod
    def get_by_id(id):
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM tax_rates WHERE id = %s", (id,))
        tax_rate = cursor.fetchone()
        cursor.close()
        conn.close()
        return tax_rate
    
    @staticmethod
    def get_active_rates():
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM tax_rates 
            WHERE is_active = 1 
            AND (effective_to IS NULL OR effective_to >= CURDATE())
            AND effective_from <= CURDATE()
            ORDER BY type, rate
        """)
        tax_rates = cursor.fetchall()
        cursor.close()
        conn.close()
        return tax_rates
    
    def save(self):
        conn = connect_db()
        cursor = conn.cursor()
        
        if self.id:
            # Update existing tax rate
            cursor.execute("""
                UPDATE tax_rates 
                SET name = %s, type = %s, rate = %s, description = %s,
                    is_active = %s, hsn_code = %s, effective_from = %s, effective_to = %s
                WHERE id = %s
            """, (self.name, self.type, self.rate, self.description,
                  self.is_active, self.hsn_code, self.effective_from, self.effective_to,
                  self.id))
        else:
            # Insert new tax rate
            cursor.execute("""
                INSERT INTO tax_rates 
                (name, type, rate, description, is_active, hsn_code, effective_from, effective_to)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (self.name, self.type, self.rate, self.description,
                  self.is_active, self.hsn_code, self.effective_from, self.effective_to))
            self.id = cursor.lastrowid
            
        conn.commit()
        cursor.close()
        conn.close()
        return self.id

# Tax Filing model
class TaxFiling:
    def __init__(self, id=None, filing_type=None, period_start=None, period_end=None, 
                 due_date=None, filing_date=None, status='Pending', collected_amount=0,
                 paid_amount=0, net_payable=0, reference_number=None, notes=None):
        self.id = id
        self.filing_type = filing_type
        self.period_start = period_start
        self.period_end = period_end
        self.due_date = due_date
        self.filing_date = filing_date
        self.status = status
        self.collected_amount = collected_amount
        self.paid_amount = paid_amount
        self.net_payable = net_payable
        self.reference_number = reference_number
        self.notes = notes
    
    @staticmethod
    def get_all():
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM tax_filing 
            ORDER BY period_end DESC, filing_type
        """)
        filings = cursor.fetchall()
        cursor.close()
        conn.close()
        return filings
    
    @staticmethod
    def get_by_id(id):
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM tax_filing WHERE id = %s", (id,))
        filing = cursor.fetchone()
        cursor.close()
        conn.close()
        return filing
    
    @staticmethod
    def get_pending():
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM tax_filing 
            WHERE status = 'Pending' AND due_date >= CURDATE()
            ORDER BY due_date ASC
        """)
        filings = cursor.fetchall()
        cursor.close()
        conn.close()
        return filings
    
    @staticmethod
    def get_overdue():
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM tax_filing 
            WHERE status = 'Pending' AND due_date < CURDATE()
            ORDER BY due_date ASC
        """)
        filings = cursor.fetchall()
        cursor.close()
        conn.close()
        return filings
    
    def save(self):
        conn = connect_db()
        cursor = conn.cursor()
        
        if self.id:
            # Update existing filing
            cursor.execute("""
                UPDATE tax_filing 
                SET filing_type = %s, period_start = %s, period_end = %s,
                    due_date = %s, filing_date = %s, status = %s,
                    collected_amount = %s, paid_amount = %s, net_payable = %s,
                    reference_number = %s, notes = %s
                WHERE id = %s
            """, (self.filing_type, self.period_start, self.period_end,
                  self.due_date, self.filing_date, self.status,
                  self.collected_amount, self.paid_amount, self.net_payable,
                  self.reference_number, self.notes, self.id))
        else:
            # Insert new filing
            cursor.execute("""
                INSERT INTO tax_filing 
                (filing_type, period_start, period_end, due_date, filing_date,
                 status, collected_amount, paid_amount, net_payable, reference_number, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (self.filing_type, self.period_start, self.period_end,
                  self.due_date, self.filing_date, self.status,
                  self.collected_amount, self.paid_amount, self.net_payable,
                  self.reference_number, self.notes))
            self.id = cursor.lastrowid
            
        conn.commit()
        cursor.close()
        conn.close()
        return self.id
