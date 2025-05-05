import streamlit as st
import pandas as pd
import numpy as np
import joblib
import bcrypt
import sqlite3
from pathlib import Path
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module='streamlit')

# ==================== AUTHENTICATION SYSTEM ====================
def init_db():
    """Initialize the SQLite database for user storage"""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT,
            email TEXT
        )
    ''')

    # Create default admin user if none exists (remove in production)
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        hashed_pw = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt())
        c.execute("INSERT OR IGNORE INTO users VALUES (?, ?, ?)", 
                 ("admin", hashed_pw, "admin@example.com"))

    conn.commit()
    conn.close()

def hash_password(password):
    """Hash a password for storage"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def verify_password(password, stored_hash):
    """Verify a password against stored hash"""
    if isinstance(stored_hash, str):
        stored_hash = stored_hash.encode('utf-8')
    return bcrypt.checkpw(password.encode('utf-8'), stored_hash)

def authenticate(username, password):
    """Check if username/password is valid"""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    return verify_password(password, result[0]) if result else False

def register_user(username, password, email):
    """Register a new user"""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        hashed_pw = hash_password(password)
        c.execute("INSERT INTO users VALUES (?, ?, ?)", 
                 (username, hashed_pw, email))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        st.error("Username already exists")
        return False
    finally:
        conn.close()

def login_section():
    """Handle login/registration flow"""
    st.experimental_rerun()
