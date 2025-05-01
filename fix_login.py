import mysql.connector
from werkzeug.security import generate_password_hash

def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="roxanne",
        database="accounting"
    )

def main():
    # Simple password for demonstration
    default_password = "password123"
    hashed_password = generate_password_hash(default_password)
    
    # Connect to database
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get all users
        cursor.execute("SELECT id, username, role FROM users")
        users = cursor.fetchall()
        
        print(f"Found {len(users)} users in database")
        
        for user in users:
            user_id = user["id"]
            username = user["username"]
            
            # Reset password for each user
            cursor.execute(
                "UPDATE users SET password_hash = %s WHERE id = %s",
                (hashed_password, user_id)
            )
            
            print(f"Reset password for {username} (ID: {user_id}) to '{default_password}'")
        
        # Commit changes
        conn.commit()
        
        # Verify the updates
        cursor.execute("SELECT id, username, LENGTH(password_hash) as hash_length FROM users")
        updated_users = cursor.fetchall()
        
        print("\nVerification of updated passwords:")
        for user in updated_users:
            print(f"User ID: {user['id']} | Username: {user['username']} | Password hash length: {user['hash_length']}")
        
        print("\n✅ All passwords have been reset to the default: " + default_password)
        print("You can now log in with any username and the password: " + default_password)
        
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main() 