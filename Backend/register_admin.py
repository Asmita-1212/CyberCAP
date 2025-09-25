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
password = input("Enter admin password: ")

# Hash the password
hashed_password = generate_password_hash(password)

# Generate MFA secret
mfa_secret = pyotp.random_base32()

# Insert admin into DB
admin_data = {
    "username": username,
    "password": hashed_password,
    "mfa_secret": mfa_secret
}
admins_collection.insert_one(admin_data)

print(f"\n✅ Admin '{username}' created successfully.")
print("MFA Secret (in case you want manual entry):", mfa_secret)

# Generate QR Code for Authenticator
totp = pyotp.TOTP(mfa_secret)
uri = totp.provisioning_uri(name=username, issuer_name="CyberCAP")
qr = qrcode.make(uri)
qr_filename = f"{username}_mfa_qr.png"
qr.save(qr_filename)

print(f"📲 QR code generated as {qr_filename}.")
print("➡ Scan it in Google Authenticator or Authy.\n")
