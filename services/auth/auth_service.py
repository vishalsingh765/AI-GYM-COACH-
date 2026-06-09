import hashlib
import secrets
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.getcwd(), "gym_trainer.db")

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str, salt: str = None) -> tuple:
    """Hash password with salt"""
    if salt is None:
        salt = secrets.token_hex(16)
    hash_obj = hashlib.sha256((password + salt).encode())
    return hash_obj.hexdigest(), salt

def verify_password(password: str, hashed_password: str, salt: str) -> bool:
    """Verify password against hash"""
    new_hash, _ = hash_password(password, salt)
    return new_hash == hashed_password

def create_user(username: str, email: str, password: str) -> dict:
    """Create a new user in the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email))
        existing = cursor.fetchone()
        if existing:
            conn.close()
            return {"success": False, "error": "Username or email already exists"}
        
        # Hash password
        hashed_pw, salt = hash_password(password)
        created_at = datetime.now().isoformat()
        
        # Insert user
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, salt, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (username, email, hashed_pw, salt, created_at))
        
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        
        return {
            "success": True,
            "user": {"id": user_id, "username": username, "email": email}
        }
    except Exception as e:
        conn.close()
        return {"success": False, "error": str(e)}

def authenticate_user(username: str, password: str) -> dict:
    """Authenticate a user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Try to find user by username or email
        cursor.execute("""
            SELECT id, username, email, password_hash, salt 
            FROM users 
            WHERE username = ? OR email = ?
        """, (username, username))
        
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return {"success": False, "error": "Invalid username/email or password"}
        
        # Verify password
        if verify_password(password, user['password_hash'], user['salt']):
            return {
                "success": True,
                "user": {
                    "id": user['id'], 
                    "username": user['username'], 
                    "email": user['email']
                }
            }
        else:
            return {"success": False, "error": "Invalid username/email or password"}
    except Exception as e:
        conn.close()
        return {"success": False, "error": f"Authentication error: {str(e)}"}

def update_user_password(user_id: int, old_password: str, new_password: str) -> dict:
    """Update user password"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get user's current password hash and salt
        cursor.execute("SELECT password_hash, salt FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return {"success": False, "error": "User not found"}
        
        # Verify old password
        if not verify_password(old_password, user['password_hash'], user['salt']):
            conn.close()
            return {"success": False, "error": "Current password is incorrect"}
        
        # Hash new password
        new_hash, new_salt = hash_password(new_password)
        
        # Update password
        cursor.execute("""
            UPDATE users 
            SET password_hash = ?, salt = ?, updated_at = ?
            WHERE id = ?
        """, (new_hash, new_salt, datetime.now().isoformat(), user_id))
        
        conn.commit()
        conn.close()
        return {"success": True}
    except Exception as e:
        conn.close()
        return {"success": False, "error": str(e)}

def create_test_user():
    """Create a test user for debugging"""
    result = create_user("testuser", "test@example.com", "password123")
    if result["success"]:
        print("Test user created: username='testuser', password='password123'")
    else:
        print(f"Test user creation: {result['error']}")