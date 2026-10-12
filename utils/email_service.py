import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL_USER = os.getenv('EMAIL_USER')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

def generate_otp():
    """Generate 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

def send_otp_email(recipient_email, otp):
    """Send OTP via email"""
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = recipient_email
        msg['Subject'] = 'SmileCare Clinic - Password Reset OTP'
        
        # Email body
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f8fafc;">
            <div style="background: linear-gradient(135deg, #07628f 0%, #5e06c2 90%); padding: 30px; border-radius: 16px; color: white; text-align: center;">
                <h2 style="margin: 0;">SmileCare Clinic</h2>
                <p style="margin: 5px 0 0;">Password Reset Verification</p>
            </div>
            <div style="background: white; padding: 30px; border-radius: 0 0 16px 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                <h3 style="color: #1e293b;">Hello,</h3>
                <p style="color: #475569; line-height: 1.6;">
                    You requested to reset your password. Use the following OTP to complete the process:
                </p>
                <div style="background: #f1f5f9; padding: 20px; border-radius: 12px; text-align: center; margin: 20px 0;">
                    <h1 style="font-size: 42px; letter-spacing: 10px; color: #07628f; font-weight: bold; margin: 0;">
                        {otp}
                    </h1>
                </div>
                <p style="color: #475569; font-size: 14px;">
                    This OTP is valid for <strong>10 minutes</strong>. If you didn't request this, please ignore this email.
                </p>
                <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;">
                <p style="color: #94a3b8; font-size: 12px; text-align: center;">
                    SmileCare Clinic &bull; Established 2006<br>
                    Opposite City Bus Stand, Main Road
                </p>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Send email
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Email error: {str(e)}")
        return False