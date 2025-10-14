# Backend/app.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from passlib.hash import bcrypt
from bson.objectid import ObjectId
from pymongo import ReturnDocument
from werkzeug.security import check_password_hash
import pyotp

from Backend.models import User, LoginUser, Complaint, AdminLogin, AdminMFA,Volunteers
from Backend.forgot_password_api import send_otp
from Backend.database import users_collection, complaints_collection, admins_collection, password_resets,volunteers

from fastapi import Body
from deep_translator import GoogleTranslator
#translate helper function
def translate_to_english(text: str) -> str:
    """
    Translates any text to English using deep-translator.
    Returns translated text; if translation fails, returns original text.
    """
    try:
        return GoogleTranslator(source='auto', target='en').translate(text)
    except Exception as e:
        print("Translation error:", e)
        return text
# ---------------- FastAPI App ----------------
app = FastAPI(title="CyberCAP Backend")
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from Backend.database import complaints_collection

# ---------------- Track Complaint Model ----------------
class TrackRequest(BaseModel):
    complaintId: str
    mobile: str

# Enable CORS (for frontend communication)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- Counter for complaint IDs ----------------
counters = password_resets.database["counters"]  # Using same DB
if counters.find_one({"_id": "complaintid"}) is None:
    counters.insert_one({"_id": "complaintid", "sequence_value": 0})

def get_next_sequence(name: str):
    counter = counters.find_one_and_update(
        {"_id": name},
        {"$inc": {"sequence_value": 1}},
        return_document=ReturnDocument.AFTER
    )
    return counter["sequence_value"]

# ---------------- OTP Store for Admin MFA ----------------
admin_otp_store = {}  # stores pending MFA sessions

# ---------------- Helper Functions ----------------
def user_helper(user) -> dict:
    return {
        "id": str(user["_id"]),
        "username": user["username"],
        "email": user["email"]
    }

def complaint_helper(complaint) -> dict:
    return {
        "id": str(complaint["_id"]),
        "complaint_id": complaint.get("complaint_id"),
        "incident_type": complaint["incident_type"],
        "incident_date": complaint["incident_date"],
        "incident_time": complaint.get("incident_time"),
        "platform": complaint["platform"],
        "description": complaint["description"],
        "suspect": complaint.get("suspect"),
        "victim": complaint["victim"],
        "attachments": complaint.get("attachments", []),
        "status": complaint.get("status", "Pending"),
        "priority": complaint.get("priority"),
        "category": complaint.get("category"),
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

    # ------------------ TRANSLATE DESCRIPTION ------------------
    original_description = complaint_data.get("description", "")
    translated_description = translate_to_english(original_description)

# Save both
    complaint_data["description"] = translated_description       # translated
    complaint_data["original_description"] = original_description # original

    # -----------------------------------------------------------

    # Generate complaint ID
    next_id = get_next_sequence("complaintid")
    complaint_data["complaint_id"] = f"CC-{next_id:05d}"
    complaint_data["status"] = "Pending"

    # Link complaint to logged-in user
    complaint_data["registered_by"] = complaint_data.get("victim", {}).get("email")

    # Insert into MongoDB
    result = complaints_collection.insert_one(complaint_data)
    
    return {
        "id": str(result.inserted_id),
        "complaint_id": complaint_data["complaint_id"],
        "message": "Complaint submitted successfully"
    }

@app.get("/complaints")
def get_complaints():
    complaints = []
    for c in complaints_collection.find():
        complaints.append(complaint_helper(c))
    return complaints

@app.get("/user_complaints/{email}")
def get_user_complaints(email: str):
    complaints = []
    for c in complaints_collection.find({"registered_by": email}):
        complaints.append(complaint_helper(c))
    return complaints

# ---------------- Admin Endpoints ----------------
@app.post("/admin-login")
def admin_login(admin: AdminLogin):
    db_admin = admins_collection.find_one({"username": admin.username})
    if not db_admin or not check_password_hash(db_admin["password"], admin.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # ✅ No new random secret needed here
    return {
        "message": "Password verified. Please enter OTP from your Authenticator app.",
        "username": admin.username
    }

@app.post("/admin-mfa")
def admin_mfa(mfa: AdminMFA):
    db_admin = admins_collection.find_one({"username": mfa.username})
    if not db_admin:
        raise HTTPException(status_code=401, detail="Admin not found")

    totp = pyotp.TOTP(db_admin["mfa_secret"])

    # ✅ Use valid_window to allow slight clock differences
    if totp.verify(mfa.otp, valid_window=1):
        return {"message": "Admin login successful"}
    else:
        raise HTTPException(status_code=401, detail="Invalid OTP")


# ---------------- Password Reset Endpoints ----------------
from pydantic import BaseModel

class ForgotPasswordSchema(BaseModel):
    email: str

class ResetPasswordSchema(BaseModel):
    email: str
    otp: str
    new_password: str

@app.post("/send-otp")
def send_otp_endpoint(data: ForgotPasswordSchema):
    user = users_collection.find_one({"email": data.email})
    if not user:
        raise HTTPException(status_code=404, detail="Email not registered")

    otp_code = send_otp(data.email)
    if otp_code:
        password_resets.update_one(
            {"email": data.email},
            {"$set": {"otp": otp_code, "created_at": datetime.utcnow()}},
            upsert=True
        )
        return {"message": "OTP sent successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send OTP")

@app.post("/reset-password")
def reset_password(data: ResetPasswordSchema):
    record = password_resets.find_one({"email": data.email})
    if not record or record["otp"] != data.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    hashed_pw = bcrypt.hash(data.new_password)
    users_collection.update_one(
        {"email": data.email},
        {"$set": {"password": hashed_pw}}
    )

    password_resets.delete_one({"email": data.email})

    return {"message": "Password reset successful"}

#complaint tracking
@app.post("/track_complaint")
def track_complaint(data: dict = Body(...)):
    complaint_id = data.get("complaintId")
    mobile = data.get("mobile")

    # Search in complaints collection
    complaint = complaints_collection.find_one({
        "complaint_id": complaint_id,
        "victim.mobile": mobile
    })

    if not complaint:
        return {"error": "Complaint not found"}

    return {
        "complaint_id": complaint["complaint_id"],
        "status": complaint.get("status", "Pending"),
        "incident_type": complaint.get("incident_type"),
        "incident_date": complaint.get("incident_date"),
        "platform": complaint.get("platform"),
        "description": complaint.get("description", "")
    }
# volunteer registration

from fastapi import Form
@app.post("/register_volunteer")
def register_volunteer(
    name: str = Form(...),
    email: str = Form(...),
    mobile: str = Form(...),
    role: str = Form(...),
    state: str = Form(...),
    expertise: str = Form(None),
    message: str = Form(...)
):
    # Check if email already exists
    if volunteers.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="Email already registered")

    volunteer_data = {
        "name": name,
        "email": email,
        "mobile": mobile,
        "role": role,
        "state": state,
        "expertise": expertise,
        "message": message,
        "registration_date": datetime.utcnow()
    }

    volunteers.insert_one(volunteer_data)
    return {"message": "✅ Registration successful! Thank you for joining CyberCAP."}


