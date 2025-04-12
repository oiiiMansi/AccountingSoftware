import mysql.connector
from mysql.connector import Error

# Database connection function
def connect_db():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="roxanne",
            database="accounting"
        )
        if conn.is_connected():
            return conn
    except Error as e:
        print(f"Error: {e}")
        return None


# Create Tables Function (initial setup)
def create_tables():
    conn = connect_db()
    if conn is None:
        print("Unable to connect to the database.")
        return
    
    try:
        cursor = conn.cursor()

        # Users Table (Login System)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            role ENUM('admin', 'accountant') NOT NULL
        )
        """)

        # Billing Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS bills (
            id INT AUTO_INCREMENT PRIMARY KEY,
            customer_name VARCHAR(255),
            amount DECIMAL(10,2),
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Expenses Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INT AUTO_INCREMENT PRIMARY KEY,
            expense_name VARCHAR(255),
            amount DECIMAL(10,2),
            category VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        conn.commit()
        print("Tables created successfully!")
    except Error as e:
        print(f"Error occurred while creating tables: {e}")
    finally:
        conn.close()


# Function to fetch data from any table using dictionary cursor
def fetch_data(query, params=None):
    conn = connect_db()
    if conn is None:
        return None
    
    try:
        cursor = conn.cursor(dictionary=True)  # Use DictCursor for easy access to column names
        cursor.execute(query, params if params else ())
        result = cursor.fetchall()
        return result
    except Error as e:
        print(f"Error occurred while fetching data: {e}")
        return None
    finally:
        conn.close()

# Example usage:
if __name__ == "__main__":
    create_tables()  # This would only run once when needed to initialize tables
