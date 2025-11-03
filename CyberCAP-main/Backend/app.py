import joblib
import os
from fastapi import HTTPException

from fastapi import FastAPI, HTTPException, UploadFile, File, Body, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from datetime import datetime
from passlib.hash import bcrypt
from bson.objectid import ObjectId
from pymongo import ReturnDocument
from werkzeug.security import check_password_hash
import pyotp
import os
import shutil
from deep_translator import GoogleTranslator

from Backend.models import User, LoginUser, Complaint, AdminLogin, AdminMFA, Volunteers
from Backend.forgot_password_api import send_otp
from Backend.database import users_collection, complaints_collection, admins_collection, password_resets, volunteers,contact_collection

# ---------------- Initialize App ----------------
app = FastAPI(title="CyberCAP Backend")


# ---------------- ML Model Loading ----------------
# Path: Backend/app.py → ../ml/category_model.pkl
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # Go one level up from Backend/
ML_DIR = os.path.join(BASE_DIR, "ml")

category_model_path = os.path.join(ML_DIR, "category_model.pkl")
priority_model_path = os.path.join(ML_DIR, "priority_model.pkl")

try:
    category_model = joblib.load(category_model_path)
    priority_model = joblib.load(priority_model_path)
    print("✅ ML Models loaded successfully from /ml folder")
except Exception as e:
    print(f"❌ Error loading ML models: {e}")
    category_model = None
    priority_model = None

def classify_complaint(description: str):
    """
    Predicts complaint category and priority using trained ML models.
    """
    if not category_model or not priority_model:
        raise HTTPException(status_code=500, detail="ML models not loaded")

    # Predict category and priority
    category_pred = category_model.predict([description])[0]
    priority_pred = priority_model.predict([description])[0]

    return {"category": category_pred, "priority": priority_pred}

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- Setup Uploads Folder ----------------
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=UPLOAD_FOLDER), name="uploads")


# ---------------- Upload Route ----------------
@app.post("/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    saved_filenames = []
    for file in files:
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        saved_filenames.append(file.filename)
    return {"filenames": saved_filenames}


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
    # Convert incoming Pydantic model to dict
    complaint_data = complaint.dict()
    complaint_data["created_at"] = datetime.utcnow().isoformat()

    # ------------------ HANDLE ATTACHMENTS ------------------
    attachments = complaint_data.get("attachments", [])
    if attachments and isinstance(attachments, list):
        saved_files = []
        for file_data in attachments:
            if hasattr(file_data, "filename"):
                file_path = os.path.join(UPLOAD_FOLDER, file_data.filename)
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file_data.file, buffer)
                saved_files.append(f"/uploads/{file_data.filename}")
            else:
                saved_files.append(file_data)
        complaint_data["attachments"] = saved_files
    else:
        complaint_data["attachments"] = []
    # ---------------------------------------------------------

    # ------------------ TRANSLATE DESCRIPTION ------------------
    original_description = complaint_data.get("description", "")
    translated_description = translate_to_english(original_description)
    complaint_data["description"] = translated_description
    complaint_data["original_description"] = original_description
    # -----------------------------------------------------------

    # ------------------ ML MODEL PREDICTION ------------------
    try:
        predictions = classify_complaint(translated_description)
        complaint_data["category"] = predictions["category"]
        complaint_data["priority"] = predictions["priority"]
        print(f"🔍 Predicted -> Category: {predictions['category']}, Priority: {predictions['priority']}")
    except Exception as e:
        print(f"⚠️ Prediction error: {e}")
        complaint_data["category"] = "Unknown"
        complaint_data["priority"] = "Normal"
    # -----------------------------------------------------------

    # Generate unique complaint ID
    next_id = get_next_sequence("complaintid")
    complaint_data["complaint_id"] = f"CC-{next_id:05d}"
    complaint_data["status"] = "Pending"

    # Link to logged-in user if applicable
    complaint_data["registered_by"] = complaint_data.get("victim", {}).get("email")

    # Save in MongoDB
    result = complaints_collection.insert_one(complaint_data)

    # Return success response
    return {
        "id": str(result.inserted_id),
        "complaint_id": complaint_data["complaint_id"],
        "message": "Complaint submitted successfully",
        "assigned_category": complaint_data["category"],
        "assigned_priority": complaint_data["priority"]
    }

@app.get("/complaints")
def get_all_complaints():
    # Fetch all complaints from MongoDB
    complaints = complaints_collection.find().sort("created_at", -1)  # latest first
    complaint_list = [complaint_helper(c) for c in complaints]
    print(f"⚡ Fetched {len(complaint_list)} complaints")
    return complaint_list
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


@app.get("/admin-info/{username}")
def get_admin_info(username: str):
    admin = admins_collection.find_one({"username": username})
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    return {
        "_id": str(admin["_id"]),
        "username": admin["username"],
        "email": admin["email"],
        "phone": admin.get("phone", None),
        "photo": admin.get("photo", None)
    }

@app.get("/complaint/{complaint_id}")
def get_complaint(complaint_id: str):
    complaint = complaints_collection.find_one({"complaint_id": complaint_id})
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    complaint["_id"] = str(complaint["_id"])
    return complaint



from bson import ObjectId

from bson import ObjectId

@app.patch("/complaint/{c_id}/status")
async def update_status(c_id: str, data: dict):
    new_status = data.get("status")
    print(f"🟡 Incoming PATCH request for complaint_id={c_id}")
    print(f"🟢 New status received: {new_status}")

    # Convert string to ObjectId
    try:
        obj_id = ObjectId(c_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid complaint ID format")

    # Find complaint by ObjectId
    complaint = complaints_collection.find_one({"_id": obj_id})
    print(f"🔍 Found complaint: {complaint}")

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    # Perform update
    result = complaints_collection.update_one(
        {"_id": obj_id},
        {"$set": {"status": new_status}}
    )

    print(f"✅ Matched {result.matched_count}, Modified {result.modified_count}")
    return {"message": "Status updated successfully"}

@app.post("/contact")
async def save_contact(
    name: str = Form(...),
    email: str = Form(...),
    subject: str = Form(""),
    message: str = Form(...)
):
    contact_data = {
        "name": name,
        "email": email,
        "subject": subject,
        "message": message,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    contact_collection.insert_one(contact_data)
    return {"status": "success", "message": "Your message has been received!"}

@app.get("/contact_messages")
async def get_contact_messages():
    messages = list(contact_collection.find({}, {"_id": 0}))
    return {"messages": messages}
@app.get("/feedback")
def get_feedback():
    feedbacks = list(contact_collection.find({}))
    for f in feedbacks:
        f["_id"] = str(f["_id"])
    return feedbacks