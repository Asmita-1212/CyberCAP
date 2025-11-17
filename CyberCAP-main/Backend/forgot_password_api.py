# backend/forgot_paaword_api.py
import smtplib
import random
from email.mime.text import MIMEText
from email.header import Header

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

def send_email_notification(receiver_email: str, subject: str, body: str):
    sender_email = "asmitatanmor12@gmail.com"
    app_password = "jrcreulhoacuflki"  # Gmail app password

    try:
        # ✅ Create a MIME email that supports UTF-8 characters
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = Header(subject, "utf-8")
        msg["From"] = sender_email
        msg["To"] = receiver_email

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, app_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())

        print(f"✅ Email sent successfully to {receiver_email}")
        return True

    except Exception as e:
        print("❌ Error sending notification:", e)
        return False
