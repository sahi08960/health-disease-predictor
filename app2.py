import streamlit as st
import sqlite3
import secrets
import time
import smtplib
from email.message import EmailMessage

# --- Configuration ---
SMTP_SERVER = "smtp.gmail.com"  # Change if not using Gmail
SMTP_PORT = 587
EMAIL_FROM = "your-email@gmail.com"  # Store in secrets.toml
EMAIL_PASSWORD = "your-app-password"  # Store in secrets.toml

# --- Database Setup ---
def init_db():
    conn = sqlite3.connect('auth.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            otp TEXT,
            otp_expiry INTEGER,
            verified BOOLEAN DEFAULT FALSE
        )
    ''')
    conn.commit()
    conn.close()

# --- Email Functions ---
def send_otp_email(email):
    """Send 6-digit OTP via email"""
    otp = f"{secrets.randbelow(999999):06d}"  # 6-digit zero-padded
    expiry = int(time.time()) + 300  # 5 minutes
    
    # Store in database
    conn = sqlite3.connect('auth.db')
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO users VALUES (?, ?, ?, FALSE)
    ''', (email, otp, expiry))
    conn.commit()
    conn.close()
    
    # Send email
    msg = EmailMessage()
    msg.set_content(f"Your verification code is: {otp}\n\nValid for 5 minutes.")
    msg['Subject'] = "Your Login OTP"
    msg['From'] = EMAIL_FROM
    msg['To'] = email
    
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Failed to send email: {e}")
        return False

# --- Authentication Flow ---
def login_section():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        st.title("📧 Email Login")
        
        # Step 1: Email Input
        if 'login_step' not in st.session_state:
            email = st.text_input("Enter Your Email")
            
            if st.button("Send OTP"):
                if "@" in email and "." in email.split("@")[-1]:
                    if send_otp_email(email):
                        st.session_state.login_step = "verify"
                        st.session_state.email = email
                        st.success("OTP sent to your email!")
                        st.experimental_rerun()
                else:
                    st.error("Please enter a valid email")
        
        # Step 2: OTP Verification
        elif st.session_state.login_step == "verify":
            otp = st.text_input("Enter 6-digit OTP")
            
            if st.button("Verify"):
                conn = sqlite3.connect('auth.db')
                c = conn.cursor()
                c.execute('''
                    SELECT otp, otp_expiry FROM users 
                    WHERE email = ?
                ''', (st.session_state.email,))
                result = c.fetchone()
                conn.close()
                
                if result and time.time() < result[1] and otp == result[0]:
                    st.session_state.authenticated = True
                    st.experimental_rerun()
                else:
                    st.error("Invalid OTP or expired")
            
            if st.button("↻ Resend OTP"):
                send_otp_email(st.session_state.email)
                st.success("New OTP sent!")
        
        st.stop()

# --- Main App ---
def main_app():
    st.title(f"Welcome! {st.session_state.email}")
    st.write("Your diabetes prediction app content here...")
    %%writefile app.py
import streamlit as st
import pandas as pd
import numpy as np
import joblib

# Load model
model = joblib.load('diabetes_model.pkl')

st.title("🔬 Diabetes Prediction App")
st.markdown("Enter the patient details to predict diabetes.")

# Input fields
preg = st.number_input("Pregnancies", min_value=0, max_value=20, step=1)
glucose = st.number_input("Glucose", min_value=0.0)
bp = st.number_input("Blood Pressure", min_value=0.0)
skin = st.number_input("Skin Thickness", min_value=0.0)
insulin = st.number_input("Insulin", min_value=0.0)
bmi = st.number_input("BMI", min_value=0.0)
dpf = st.number_input("Diabetes Pedigree Function", min_value=0.0)
age = st.number_input("Age", min_value=1, max_value=120)

if st.button("Predict"):
    input_data = np.array([[preg, glucose, bp, skin, insulin, bmi, dpf, age]])
    prediction = model.predict(input_data)

    if prediction[0] == 1:
        st.error("⚠️ The person is likely to have diabetes.")
    else:
        st.success("✅ The person is not likely to have diabetes.")

    
    if st.button("Logout"):
        st.session_state.clear()
        st.experimental_rerun()

# --- Run App ---
if __name__ == "__main__":
    init_db()
    login_section()
    main_app()
