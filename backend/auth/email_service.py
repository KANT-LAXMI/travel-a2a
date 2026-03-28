"""
Email Service for OTP
======================
Sends OTP emails for password reset functionality.

Uses Gmail SMTP for sending emails.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import os
from dotenv import load_dotenv
load_dotenv()



class EmailService:
    """
    Email service for sending OTP emails.
    
    Configuration:
        Set these environment variables:
        - EMAIL_HOST: SMTP server (default: smtp.gmail.com)
        - EMAIL_PORT: SMTP port (default: 587)
        - EMAIL_USER: Your email address
        - EMAIL_PASSWORD: Your email app password
    """
    
    def __init__(self):
        self.smtp_host = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('EMAIL_PORT', 587))
        self.email_user = os.getenv('EMAIL_USER', '')
        self.email_password = os.getenv('EMAIL_PASSWORD', '')
        
        if not self.email_user or not self.email_password:
            print("⚠️  [EMAIL] Warning: Email credentials not configured")
            print("⚠️  [EMAIL] Set EMAIL_USER and EMAIL_PASSWORD environment variables")
    
    def send_otp_email(self, to_email: str, otp: str, user_name: str = "User") -> bool:
        """
        Send OTP email to user.
        
        Args:
            to_email (str): Recipient email address
            otp (str): 6-digit OTP code
            user_name (str): User's name for personalization
        
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        print(f"📧 [EMAIL] Sending OTP to: {to_email}")
        
        if not self.email_user or not self.email_password:
            print("❌ [EMAIL] Email service not configured")
            # For development: print OTP to console
            print(f"🔐 [DEV MODE] OTP for {to_email}: {otp}")
            return True  # Return True in dev mode
        
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = "Password Reset OTP - Anywhere App"
            message["From"] = f"Anywhere App <{self.email_user}>"
            message["To"] = to_email
            
            # Email body (HTML)
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                    }}
                    .container {{
                        background: #ffffff;
                        border-radius: 12px;
                        padding: 40px;
                        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
                    }}
                    .logo {{
                        text-align: center;
                        margin-bottom: 30px;
                    }}
                    .logo-circle {{
                        width: 60px;
                        height: 60px;
                        background: #2196F3;
                        border-radius: 50%;
                        display: inline-block;
                        margin-bottom: 10px;
                    }}
                    .logo-text {{
                        font-size: 24px;
                        font-weight: 600;
                        color: #1a1a1a;
                    }}
                    h1 {{
                        color: #1a1a1a;
                        font-size: 24px;
                        margin-bottom: 20px;
                    }}
                    .otp-box {{
                        background: #f5f7fa;
                        border: 2px dashed #2196F3;
                        border-radius: 8px;
                        padding: 30px;
                        text-align: center;
                        margin: 30px 0;
                    }}
                    .otp-code {{
                        font-size: 36px;
                        font-weight: 700;
                        color: #2196F3;
                        letter-spacing: 8px;
                        font-family: 'Courier New', monospace;
                    }}
                    .warning {{
                        background: #fff3cd;
                        border-left: 4px solid #ffc107;
                        padding: 15px;
                        margin: 20px 0;
                        border-radius: 4px;
                    }}
                    .footer {{
                        text-align: center;
                        margin-top: 30px;
                        padding-top: 20px;
                        border-top: 1px solid #e0e0e0;
                        color: #999;
                        font-size: 14px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="logo">
                        <div class="logo-circle"></div>
                        <div class="logo-text">Anywhere app.</div>
                    </div>
                    
                    <h1>Password Reset Request</h1>
                    
                    <p>Hi {user_name},</p>
                    
                    <p>We received a request to reset your password for your Anywhere App account. Use the OTP code below to reset your password:</p>
                    
                    <div class="otp-box">
                        <div style="color: #666; font-size: 14px; margin-bottom: 10px;">Your OTP Code</div>
                        <div class="otp-code">{otp}</div>
                    </div>
                    
                    <div class="warning">
                        <strong>⚠️ Security Notice:</strong>
                        <ul style="margin: 10px 0 0 0; padding-left: 20px;">
                            <li>This OTP is valid for <strong>10 minutes</strong></li>
                            <li>Never share this code with anyone</li>
                            <li>If you didn't request this, please ignore this email</li>
                        </ul>
                    </div>
                    
                    <p>If you didn't request a password reset, you can safely ignore this email. Your password will remain unchanged.</p>
                    
                    <div class="footer">
                        <p>© 2024 Anywhere App. All rights reserved.</p>
                        <p>This is an automated email, please do not reply.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Attach HTML body
            html_part = MIMEText(html_body, "html")
            message.attach(html_part)
            
            # Send email
            print(f"📤 [EMAIL] Connecting to SMTP server: {self.smtp_host}:{self.smtp_port}")
            
            # Use SSL for port 465, TLS for port 587
            if self.smtp_port == 465:
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port) as server:
                    server.login(self.email_user, self.email_password)
                    server.send_message(message)
            else:
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.email_user, self.email_password)
                    server.send_message(message)
            
            print(f"✅ [EMAIL] OTP sent successfully to: {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ [EMAIL] Failed to send email: {e}")
            # For development: print OTP to console as fallback
            print(f"🔐 [DEV MODE] OTP for {to_email}: {otp}")
            return True  # Return True in dev mode
    
    def send_password_changed_email(self, to_email: str, user_name: str = "User") -> bool:
        """
        Send confirmation email after password change.
        
        Args:
            to_email (str): Recipient email address
            user_name (str): User's name
        
        Returns:
            bool: True if email sent successfully
        """
        print(f"📧 [EMAIL] Sending password change confirmation to: {to_email}")
        
        if not self.email_user or not self.email_password:
            print("⚠️  [EMAIL] Email service not configured (skipping confirmation email)")
            return True
        
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = "Password Changed Successfully - Anywhere App"
            message["From"] = f"Anywhere App <{self.email_user}>"
            message["To"] = to_email
            
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                    }}
                    .container {{
                        background: #ffffff;
                        border-radius: 12px;
                        padding: 40px;
                        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
                    }}
                    .success-icon {{
                        text-align: center;
                        font-size: 60px;
                        margin-bottom: 20px;
                    }}
                    h1 {{
                        color: #1a1a1a;
                        text-align: center;
                        margin-bottom: 20px;
                    }}
                    .alert {{
                        background: #d4edda;
                        border-left: 4px solid #28a745;
                        padding: 15px;
                        margin: 20px 0;
                        border-radius: 4px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="success-icon">✅</div>
                    <h1>Password Changed Successfully</h1>
                    
                    <p>Hi {user_name},</p>
                    
                    <div class="alert">
                        Your password has been changed successfully. You can now log in with your new password.
                    </div>
                    
                    <p>If you didn't make this change, please contact support immediately.</p>
                    
                    <p style="text-align: center; margin-top: 30px;">
                        <a href="http://localhost:3000/login" style="background: #2196F3; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; display: inline-block;">
                            Log In Now
                        </a>
                    </p>
                </div>
            </body>
            </html>
            """
            
            html_part = MIMEText(html_body, "html")
            message.attach(html_part)
            
            # Use SSL for port 465, TLS for port 587
            if self.smtp_port == 465:
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port) as server:
                    server.login(self.email_user, self.email_password)
                    server.send_message(message)
            else:
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.email_user, self.email_password)
                    server.send_message(message)
            
            print(f"✅ [EMAIL] Confirmation sent to: {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ [EMAIL] Failed to send confirmation: {e}")
            return False


# Singleton instance
email_service = EmailService()
