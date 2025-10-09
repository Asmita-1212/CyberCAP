from pymongo import MongoClient
from werkzeug.security import generate_password_hash
import pyotp
import qrcode

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["cybercap"]
admins_collection = db["admins"]

# Admin credentials input
username = input("Enter admin username: ")
email = input("Enter admin email: ")
password = input("Enter admin password: ")

# Hash the password
hashed_password = generate_password_hash(password)

# Generate MFA secret
mfa_secret = pyotp.random_base32()

# Insert admin into DB
admin_data = {
    "username": username,
    "email": email,
    "password": hashed_password,
    "mfa_secret": mfa_secret
}
admins_collection.insert_one(admin_data)

print(f"\n✅ Admin '{username}' created successfully.")
print("📧 Email:", email)
print("🔐 MFA Secret (manual entry):", mfa_secret)

# Generate QR Code for Authenticator
totp = pyotp.TOTP(mfa_secret)
uri = totp.provisioning_uri(name=f"{username} ({email})", issuer_name="CyberCAP")
qr = qrcode.make(uri)
qr_filename = f"{username}_mfa_qr.png"
qr.save(qr_filename)

print(f"📲 QR code generated as {qr_filename}.")
print("➡ Scan it using Google Authenticator or Authy.\n")
