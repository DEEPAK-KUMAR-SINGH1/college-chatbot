from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
import mysql.connector
import random
import smtplib
from email.message import EmailMessage
from passlib.context import CryptContext
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# DB Connection
def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Kashyap@1100",
        database="auth_system"
    )

# Models
class Signup(BaseModel):
    username: str
    email: EmailStr
    password: str

class VerifyOTP(BaseModel):
    email: EmailStr
    otp: str

# Generate OTP
def generate_otp():
    return str(random.randint(100000, 999999))

# Send Email
def send_otp_email(email, otp):
    msg = EmailMessage()
    msg.set_content(f"Your OTP is {otp}")
    msg["Subject"] = "OTP Verification"
    msg["From"] = "kashyap040098@gmail.com"
    msg["To"] = email

    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login("kashyap040098@gmail.com", "dytjcfutjvjqutif")
    server.send_message(msg)
    server.quit()

@app.post("/signup")
def signup(user: Signup):
    if not user.email.endswith("@gmail.com"):
        raise HTTPException(status_code=400, detail="Only Gmail allowed")

    otp = str(generate_otp()).strip()
    hashed_password = pwd_context.hash(user.password)

    conn = get_db()
    cursor = conn.cursor()

    # Check if user already exists
    cursor.execute("SELECT email FROM users WHERE email=%s", (user.email,))
    existing = cursor.fetchone()

    if existing:
        # Update OTP if user already exists
        cursor.execute(
            "UPDATE users SET otp=%s WHERE email=%s",
            (otp, user.email)
        )
    else:
        cursor.execute(
    "INSERT INTO users (username, email, password, otp, is_verified) VALUES (%s,%s,%s,%s,%s)",
    (user.username, user.email, hashed_password, otp, False)
)


    conn.commit()

    try:
        send_otp_email(user.email, otp)
    except Exception as e:
        print("EMAIL ERROR:", e)
        raise HTTPException(status_code=500, detail="Email sending failed")

    return {"message": "OTP sent successfully"}


@app.post("/verify-otp")
def verify_otp(data: VerifyOTP):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT otp FROM users WHERE email=%s", (data.email,))
    result = cursor.fetchone()

    if not result:
        raise HTTPException(status_code=404, detail="User not found")

    stored_otp = str(result[0]).strip()
    entered_otp = str(data.otp).strip()

    print("Stored OTP:", stored_otp)
    print("Entered OTP:", entered_otp)

    if stored_otp != entered_otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    cursor.execute(
        "UPDATE users SET is_verified=TRUE WHERE email=%s",
        (data.email,)
    )
    conn.commit()

    return {"message": "User verified successfully"}

class Login(BaseModel):
    email: EmailStr
    password: str


@app.post("/login")
def login(user: Login):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT password, is_verified FROM users WHERE email=%s",
        (user.email,)
    )
    result = cursor.fetchone()

    if not result:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    stored_password, is_verified = result

    print("DB is_verified value:", is_verified)  # DEBUG

    if is_verified != 1:
        raise HTTPException(status_code=403, detail="Verify your email first")

    if not pwd_context.verify(user.password, stored_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return {"message": "Login successful"}



class ForgotPassword(BaseModel):
    email: EmailStr


@app.post("/forgot-password")
def forgot_password(data: ForgotPassword):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT email FROM users WHERE email=%s", (data.email,))
    user = cursor.fetchone()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    otp = generate_otp()

    cursor.execute(
        "UPDATE users SET reset_otp=%s WHERE email=%s",
        (otp, data.email)
    )
    conn.commit()

    send_otp_email(data.email, otp)

    return {"message": "Reset OTP sent to email"}

class ResetPassword(BaseModel):
    email: EmailStr
    otp: str
    new_password: str


@app.post("/reset-password")
def reset_password(data: ResetPassword):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT reset_otp FROM users WHERE email=%s", (data.email,))
    result = cursor.fetchone()

    if not result:
        raise HTTPException(status_code=404, detail="User not found")

    stored_otp = str(result[0]).strip()

    if stored_otp != str(data.otp).strip():
        raise HTTPException(status_code=400, detail="Invalid OTP")

    hashed_password = pwd_context.hash(data.new_password)

    cursor.execute(
        "UPDATE users SET password=%s, reset_otp=NULL WHERE email=%s",
        (hashed_password, data.email)
    )
    conn.commit()

    return {"message": "Password updated successfully"}
