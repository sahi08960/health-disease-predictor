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
        c.execute("INSERT INTO users VALUES (?, ?, ?)", 
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
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'show_login' not in st.session_state:
        st.session_state.show_login = True

    if not st.session_state.logged_in:
        if st.session_state.show_login:
            # Login Form
            st.title("🔐 Diabetes Prediction App Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")

            if st.button("Login"):
                if authenticate(username, password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.experimental_rerun()
                else:
                    st.error("Invalid username or password")

            if st.button("Register New Account"):
                st.session_state.show_login = False
                st.experimental_rerun()

            st.stop()
        else:
            # Registration Form
            st.title("📝 Create New Account")
            new_username = st.text_input("Choose Username")
            new_email = st.text_input("Email")
            new_password = st.text_input("Choose Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")

            if st.button("Register"):
                if new_password == confirm_password:
                    if register_user(new_username, new_password, new_email):
                        st.success("Registration successful! Please login.")
                        st.session_state.show_login = True
                        st.experimental_rerun()
                else:
                    st.error("Passwords don't match")

            if st.button("Back to Login"):
                st.session_state.show_login = True
                st.experimental_rerun()

            st.stop()

# ==================== INITIALIZE AND LOAD ====================
init_db()
login_section()

model = joblib.load('/content/diabetes_model.pkl')

# ==================== SIDEBAR INFO ====================
st.sidebar.title("ℹ️ About")
st.sidebar.info("""
This app uses a machine learning model to predict the likelihood of diabetes based on:
- Glucose
- BMI
- Age
- Insulin
- Blood Pressure
- Skin Thickness
- Diabetes Pedigree
- Pregnancies

Built with ❤️ using Streamlit.
""")

# ==================== MAIN UI ====================
# Logo (optional)
st.image("https://cdn-icons-png.flaticon.com/512/2920/2920388.png", width=80)

# Title and user greeting
st.markdown("<h1 style='text-align: center; color: teal;'>🔬 Diabetes Prediction App</h1>", unsafe_allow_html=True)

# Input fields layout
col1, col2 = st.columns(2)
with col1:
    preg = st.number_input("Pregnancies", min_value=0, max_value=20, step=1)
    glucose = st.number_input("Glucose", min_value=0.0)
    bp = st.number_input("Blood Pressure", min_value=0.0)
    skin = st.number_input("Skin Thickness", min_value=0.0)
with col2:
    insulin = st.number_input("Insulin", min_value=0.0)
    bmi = st.number_input("BMI", min_value=0.0)
    dpf = st.number_input("Diabetes Pedigree Function", min_value=0.0)
    age = st.number_input("Age", min_value=1, max_value=120)

# Prediction button
if st.button("Predict"):
    input_data = np.array([[preg, glucose, bp, skin, insulin, bmi, dpf, age]])
    prediction = model.predict(input_data)

    if prediction[0] == 1:
        st.markdown("<div style='background-color:#ffe6e6;padding:10px;border-radius:10px'><h4 style='color:red;'>⚠️ The model predicts that the person <b>has diabetes</b>.</h4></div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='background-color:#e6ffe6;padding:10px;border-radius:10px'><h4 style='color:green;'>✅ The model predicts that the person <b>does NOT have diabetes</b>.</h4></div>", unsafe_allow_html=True)

# Logout button
if st.button("Logout"):
    st.session_state.logged_in = False
    st.experimental_rerun()
