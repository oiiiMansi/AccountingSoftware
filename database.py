import mysql.connector


def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="roxanne",
        database="accounting"
    )

def create_tables():
    conn = connect_db()
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
    conn.close()
