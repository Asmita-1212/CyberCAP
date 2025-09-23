from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["cybercap"]

users_collection = db["users"]
complaints_collection = db["complaints"]
admins_collection = db["admins"]   # 🔐 New collection for admins
