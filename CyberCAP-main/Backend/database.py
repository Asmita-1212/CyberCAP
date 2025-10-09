from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["cybercap"]

# New collection for password reset OTPs
password_resets = db["password_resets"]

# Optional: auto-delete OTPs after 5 minutes
password_resets.create_index("created_at", expireAfterSeconds=300)

users_collection = db["users"]
complaints_collection = db["complaints"]
admins_collection = db["admins"]   # 🔐 New collection for admins
volunteers = db["volunteers"] #volunteer registration
