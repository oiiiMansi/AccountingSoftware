from werkzeug.security import generate_password_hash
import mysql.connector

def connect_db():
    """
    Establish a connection to the MySQL 'accounting' database.
    """
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="roxanne",
        database="accounting"
    )

# Connect to the database
conn = connect_db()
cursor = conn.cursor()

# Fetch all usernames and passwords from the users table
cursor.execute("SELECT username, password FROM users")
users = cursor.fetchall()

# Display passwords before update
print("\n[Before Update] Stored Passwords:")
for user in users:
    print(f"Username: {user[0]}, Password: {user[1]}")

# Hash and update plaintext passwords
for username, plain_text_password in users:
    # Check if password is already hashed to avoid double hashing
    if not plain_text_password.startswith("pbkdf2:sha256$"):
        # Hash the plaintext password using Werkzeug's generate_password_hash
        hashed_password = generate_password_hash(plain_text_password)
        # Update the user's password in the database
        cursor.execute("UPDATE users SET password = %s WHERE username = %s", (hashed_password, username))

# Commit the changes to the database
conn.commit()

# Fetch and display the updated (hashed) passwords
cursor.execute("SELECT username, password FROM users")
updated_users = cursor.fetchall()

print("\n[After Update] Stored Passwords:")
for user in updated_users:
    print(f"Username: {user[0]}, Password: {user[1]}")

# Close the cursor and database connection
cursor.close()
conn.close()

print("\n✅ Passwords updated successfully!")
