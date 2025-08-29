from fastapi import APIRouter, HTTPException
from Backend.database import users_collection
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta


router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "yoursecretkey"
ALGORITHM = "HS256"

@router.post("/register")
def register(username: str, email: str, password: str):
    # Check if user already exists
    if users_collection.find_one({"username": username}):
        raise HTTPException(status_code=400, detail="Username already exists")
    
    hashed_pw = pwd_context.hash(password)
    new_user = {
        "username": username,
        "email": email,
        "password": hashed_pw,
        "created_at": datetime.utcnow()
    }
    users_collection.insert_one(new_user)
    return {"msg": "User registered successfully!"}

@router.post("/login")
def login(username: str, password: str):
    user = users_collection.find_one({"username": username})
    if not user or not pwd_context.verify(password, user["password"]):
        raise HTTPException(status_code=400, detail="Invalid username or password")

    # Create JWT token
    token_data = {
        "sub": user["username"],
        "exp": datetime.utcnow() + timedelta(minutes=30)
    }
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}
