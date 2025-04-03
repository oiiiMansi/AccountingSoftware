from werkzeug.security import generate_password_hash
import mysql.connector

def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="roxanne",
        database="accounting"
    )

# Connect to database
conn = connect_db()
cursor = conn.cursor()

# Fetch all users
cursor.execute("SELECT username, password FROM users")
users = cursor.fetchall()

print("\n[Before Update] Stored Passwords:")
for user in users:
    print(f"Username: {user[0]}, Password: {user[1]}")

# Update passwords with hashing
for username, plain_text_password in users:
    if not plain_text_password.startswith("pbkdf2:sha256$"):  # Avoid double hashing
        hashed_password = generate_password_hash(plain_text_password)
        cursor.execute("UPDATE users SET password = %s WHERE username = %s", (hashed_password, username))

conn.commit()

# Fetch updated passwords
cursor.execute("SELECT username, password FROM users")
updated_users = cursor.fetchall()

print("\n[After Update] Stored Passwords:")
for user in updated_users:
    print(f"Username: {user[0]}, Password: {user[1]}")

cursor.close()
conn.close()
print("\n✅ Passwords updated successfully!")
