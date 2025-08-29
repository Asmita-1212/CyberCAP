# Backend/app.py
from fastapi import FastAPI, HTTPException
from Backend.models import User, Complaint, LoginUser
from Backend.database import users_collection, complaints_collection
from bson import ObjectId
from passlib.hash import bcrypt
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from Backend.forgot_password_api import send_otp

app = FastAPI()
# Your email config
EMAIL_ADDRESS = "manemahesh0306@gmail.com"
EMAIL_PASSWORD = "hwky bmux rsvi krpx"   # From Google App Passwords

def send_email(to_email, subject, message):
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(MIMEText(message, "plain"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print("Error sending email:", e)
        return False

# Temporary in-memory OTP store
otp_store = {}

class OTPRequest(BaseModel):
    email: str

class ResetRequest(BaseModel):
    email: str
    otp: str
    new_password: str

@app.post("/send-otp")
def send_otp(request: OTPRequest):
    otp = str(random.randint(100000, 999999))  # 6-digit OTP
    otp_store[request.email] = otp

    subject = "CyberCAP - Password Reset OTP"
    message = f"Your OTP for password reset is: {otp}\nThis OTP is valid for 5 minutes."

    if send_email(request.email, subject, message):
        return {"message": "OTP sent to your email"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send OTP. Try again.")


@app.post("/reset-password")
def reset_password(request: ResetRequest):
    if request.email not in otp_store or otp_store[request.email] != request.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # TODO: Update password in MongoDB
    # users.update_one({"email": request.email}, {"$set": {"password": hash_function(request.new_password)}})

    del otp_store[request.email]  # Remove OTP after use
    return {"message": "Password reset successful"}


# ✅ Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all origins (for testing)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper functions
def user_helper(user) -> dict:
    return {
        "id": str(user["_id"]),
        "username": user["username"],
        "email": user["email"]
    }

def complaint_helper(complaint) -> dict:
    return {
        "id": str(complaint["_id"]),
        "user_id": complaint["user_id"],
        "complaint_text": complaint["complaint_text"],
        "attachment": complaint.get("attachment")
    }

# ✅ Register user
@app.post("/register")
def register(user: User):
    if users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already exists")

    hashed_pw = bcrypt.hash(user.password)   # hash the password
    user_data = user.dict()
    user_data["password"] = hashed_pw        # replace raw with hash

    result = users_collection.insert_one(user_data)
    return {"id": str(result.inserted_id), "message": "User registered successfully"}

# ✅ Login user
@app.post("/login")
def login(user: LoginUser):   # only email + password
    db_user = users_collection.find_one({"email": user.email})
    if not db_user or not bcrypt.verify(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"message": "Login successful", "user": user_helper(db_user)}

# ✅ Submit complaint
@app.post("/complaint")
def create_complaint(complaint: Complaint):
    result = complaints_collection.insert_one(complaint.dict())
    return {"id": str(result.inserted_id), "message": "Complaint submitted successfully"}

# ✅ Get all complaints
@app.get("/complaints")
def get_complaints():
    complaints = []
    for complaint in complaints_collection.find():
        complaints.append(complaint_helper(complaint))
    return complaints
