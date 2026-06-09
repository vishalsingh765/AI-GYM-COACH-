import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.getcwd(), "gym_trainer.db")

def get_db_connection():
    """Get database connection with row factory"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with new schema"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT,
            last_login TEXT
        )
    """)
    
    # Create sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    # Create exercises table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            exercise_name TEXT NOT NULL,
            reps INTEGER NOT NULL,
            sets INTEGER NOT NULL,
            time INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    conn.commit()
    conn.close()

def add_exercise(user_id: int, exercise_name: str, reps: int, sets: int, time_taken: int):
    """Add exercise record to database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO exercises (user_id, exercise_name, reps, sets, time, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, exercise_name, reps, sets, time_taken, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()

def get_users_exercises(user_id: int):
    """Get all exercises for a user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT exercise_name, reps, sets, time, created_at
        FROM exercises
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,))
    
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_user_stats(user_id: int):
    """Get user statistics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total_workouts,
            SUM(reps) as total_reps,
            SUM(sets) as total_sets,
            SUM(time) as total_time
        FROM exercises
        WHERE user_id = ?
    """, (user_id,))
    
    stats = cursor.fetchone()
    conn.close()
    
    if stats and stats['total_workouts'] is not None:
        return {
            "total_workouts": stats['total_workouts'],
            "total_reps": stats['total_reps'] if stats['total_reps'] else 0,
            "total_sets": stats['total_sets'] if stats['total_sets'] else 0,
            "total_time": stats['total_time'] if stats['total_time'] else 0
        }
    else:
        return {
            "total_workouts": 0,
            "total_reps": 0,
            "total_sets": 0,
            "total_time": 0
        }

def get_or_create_user_legacy(username: str):
    """Legacy function for backward compatibility"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, username FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    
    if not user:
        import secrets
        import hashlib
        
        default_password = secrets.token_hex(16)
        hash_obj = hashlib.sha256((default_password + username).encode())
        password_hash = hash_obj.hexdigest()
        
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, salt, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (username, f"{username}@temp.com", password_hash, username, datetime.now().isoformat()))
        
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return {"id": user_id, "username": username}
    
    conn.close()
    return {"id": user['id'], "username": user['username']}