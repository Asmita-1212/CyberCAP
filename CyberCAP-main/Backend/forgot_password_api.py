# backend/forgot_paaword_api.py
import smtplib
import random

def send_otp(receiver_email: str) -> str:
    otp = str(random.randint(100000, 999999))

    sender_email = "asmitatanmor12@gmail.com"
    app_password = "jrcreulhoacuflki"  # 🔑 not your normal Gmail password

    subject = "Your OTP for CyberCAP Password Reset"
    body = f"Your OTP is: {otp}"
    message = f"Subject: {subject}\n\n{body}"

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, app_password)
            server.sendmail(sender_email, receiver_email, message)
        print("✅ OTP sent:", otp)
        return otp
    except Exception as e:
        print("❌ Error sending email:", e)
        return None
