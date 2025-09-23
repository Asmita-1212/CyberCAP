# Backend/app.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime
from bson.objectid import ObjectId
import pyotp
from werkzeug.security import check_password_hash
from passlib.hash import bcrypt
from Backend.database import users_collection, complaints_collection, admins_collection

# ---------------- FastAPI App ----------------
app = FastAPI(title="CyberCAP Backend")

# Enable CORS (for testing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- OTP Stores ----------------
admin_otp_store = {}  # stores pending MFA sessions
otp_store = {}        # for password reset emails (if used)

# ---------------- Models ----------------
class User(BaseModel):
    username: str
    email: str
    password: str

class LoginUser(BaseModel):
    email: str
    password: str

class Complaint(BaseModel):
    user_id: str
    complaint_text: str
    attachment: list = []  # optional list of file URLs/paths

class AdminLogin(BaseModel):
    username: str
    password: str

class AdminMFA(BaseModel):
    username: str
    otp: str

# ---------------- Helpers ----------------
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
        "attachment": complaint.get("attachment"),
        "created_at": complaint.get("created_at")
    }

# ---------------- User Endpoints ----------------
@app.post("/register")
def register(user: User):
    if users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already exists")
    
    hashed_pw = bcrypt.hash(user.password)
    user_data = user.dict()
    user_data["password"] = hashed_pw

    result = users_collection.insert_one(user_data)
    return {"id": str(result.inserted_id), "message": "User registered successfully"}

@app.post("/login")
def login(user: LoginUser):
    db_user = users_collection.find_one({"email": user.email})
    if not db_user or not bcrypt.verify(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return {"message": "Login successful", "user": user_helper(db_user)}

# ---------------- Complaint Endpoints ----------------
@app.post("/complaint")
def create_complaint(complaint: Complaint):
    complaint_data = complaint.dict()
    complaint_data["created_at"] = datetime.utcnow().isoformat()
    result = complaints_collection.insert_one(complaint_data)
    return {"id": str(result.inserted_id), "message": "Complaint submitted successfully"}

@app.get("/complaints")
def get_complaints():
    complaints = []
    for c in complaints_collection.find():
        complaints.append(complaint_helper(c))
    return complaints

# ---------------- Admin Endpoints ----------------
@app.post("/admin-login")
def admin_login(admin: AdminLogin):
    db_admin = admins_collection.find_one({"username": admin.username})
    if not db_admin or not check_password_hash(db_admin["password"], admin.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    otp_token = pyotp.random_base32()
    admin_otp_store[admin.username] = otp_token
    return {
        "message": "Password verified. Enter OTP from Authenticator app.",
        "username": admin.username
    }

@app.post("/admin-mfa")
def admin_mfa(mfa: AdminMFA):
    db_admin = admins_collection.find_one({"username": mfa.username})
    if not db_admin:
        raise HTTPException(status_code=401, detail="Admin not found")

    totp = pyotp.TOTP(db_admin["mfa_secret"])
    if totp.verify(mfa.otp):
        if mfa.username in admin_otp_store:
            del admin_otp_store[mfa.username]
        return {"message": "Admin login successful"}
    else:
        raise HTTPException(status_code=401, detail="Invalid OTP")
