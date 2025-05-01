from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
import getpass
import sys

def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="roxanne",
        database="accounting"
    )

def show_users():
    """Display all users in the database"""
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, username, role, password_hash FROM users")
    users = cursor.fetchall()
    
    print("\nCurrent users in database:")
    print("=" * 50)
    for user in users:
        print(f"ID: {user['id']} | Username: {user['username']} | Role: {user['role']} | Password hash length: {len(user['password_hash'] or '')}")
    
    cursor.close()
    conn.close()

def reset_password():
    """Reset password for a specific user"""
    username = input("\nEnter username to reset password: ")
    
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    
    # Check if user exists
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    
    if not user:
        print(f"User '{username}' not found!")
        cursor.close()
        conn.close()
        return
    
    # Get new password
    password = getpass.getpass("Enter new password: ")
    confirm_password = getpass.getpass("Confirm new password: ")
    
    if password != confirm_password:
        print("Passwords don't match!")
        return
    
    # Hash and update password
    hashed_password = generate_password_hash(password)
    cursor.execute("UPDATE users SET password_hash = %s WHERE username = %s", 
                   (hashed_password, username))
    conn.commit()
    
    print(f"\n✅ Password reset successfully for {username}!")
    cursor.close()
    conn.close()

def test_login():
    """Test login for a user"""
    username = input("\nEnter username to test: ")
    password = getpass.getpass("Enter password: ")
    
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    
    if not user:
        print(f"User '{username}' not found!")
        cursor.close()
        conn.close()
        return
    
    if check_password_hash(user["password_hash"], password):
        print(f"\n✅ Login successful for {username}!")
    else:
        print("\n❌ Login failed - incorrect password!")
    
    cursor.close()
    conn.close()

def add_user():
    """Add a new user to the database"""
    username = input("\nEnter new username: ")
    password = getpass.getpass("Enter password: ")
    confirm_password = getpass.getpass("Confirm password: ")
    
    if password != confirm_password:
        print("Passwords don't match!")
        return
    
    print("\nSelect role:")
    print("1. Admin")
    print("2. Accountant")
    print("3. Viewer")
    role_choice = input("Enter choice (1-3): ")
    
    role_map = {
        "1": "admin",
        "2": "accountant",
        "3": "viewer"
    }
    
    if role_choice not in role_map:
        print("Invalid role choice!")
        return
    
    role = role_map[role_choice]
    hashed_password = generate_password_hash(password)
    
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        # Check if username already exists
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            print(f"Username '{username}' already exists!")
            return
            
        # Insert new user
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
                      (username, hashed_password, role))
        conn.commit()
        print(f"\n✅ User '{username}' added successfully with role '{role}'!")
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        cursor.close()
        conn.close()

def main_menu():
    """Display main menu"""
    while True:
        print("\n=== Authentication Debugging Tool ===")
        print("1. Show all users")
        print("2. Reset user password")
        print("3. Test login")
        print("4. Add new user")
        print("5. Exit")
        
        choice = input("\nEnter choice (1-5): ")
        
        if choice == "1":
            show_users()
        elif choice == "2":
            reset_password()
        elif choice == "3":
            test_login()
        elif choice == "4":
            add_user()
        elif choice == "5":
            print("Exiting...")
            sys.exit(0)
        else:
            print("Invalid choice!")

if __name__ == "__main__":
    main_menu() 