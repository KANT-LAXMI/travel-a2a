"""
Password Reset Module
=====================
Handles forgot password functionality with OTP verification.

Features:
- Generate 6-digit OTP
- Store OTP with expiration (10 minutes)
- Verify OTP
- Reset password
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import random
import string
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
import bcrypt
from backend.config import Config
from backend.auth.db_models import get_user_by_email
from backend.auth.email_service import email_service

logger = logging.getLogger(__name__)


class PasswordResetManager:
    """
    Manages password reset operations with OTP verification.
    """
    
    def __init__(self):
        self._init_otp_table()
    
    def _init_otp_table(self):
        """Create OTP storage table if it doesn't exist."""
        conn = psycopg2.connect(Config.DATABASE_URL)
        cursor = conn.cursor()
        
        # Table is now created by schema.sql, just verify it exists
        cursor.execute("""
            SELECT tablename FROM pg_tables 
            WHERE tablename = 'password_reset_otps'
        """)
        
        if cursor.fetchone():
            logger.info("[RESET] OTP table verified")
        else:
            logger.warning("[RESET] OTP table not found, creating...")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS password_reset_otps (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) NOT NULL,
                    otp VARCHAR(10) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    used INTEGER DEFAULT 0,
                    UNIQUE(email, otp)
                )
            ''')
            conn.commit()
            logger.info("[RESET] OTP table created")
        
        conn.close()
    
    def generate_otp(self) -> str:
        """
        Generate a random 6-digit OTP.
        
        Returns:
            str: 6-digit OTP code
        """
        return ''.join(random.choices(string.digits, k=6))
    
    def request_password_reset(self, email: str) -> Tuple[bool, str]:
        """
        Initiate password reset by sending OTP to user's email.
        
        Args:
            email (str): User's email address
        
        Returns:
            tuple: (success: bool, message: str)
        
        Process:
            1. Check if user exists
            2. Generate 6-digit OTP
            3. Store OTP in database with 10-minute expiration
            4. Send OTP via email
            5. Return success/failure
        """
        print("\n" + "="*70)
        print("🔐 [RESET] Password reset request received")
        print(f"📧 [RESET] Email: {email}")
        
        email = email.strip().lower()
        
        # Check if user exists
        user = get_user_by_email(email)
        if not user:
            print(f"❌ [RESET] User not found: {email}")
            # Don't reveal if email exists or not (security)
            return True, "If this email is registered, you will receive an OTP"
        
        print(f"✅ [RESET] User found: {user.first_name} {user.last_name} (ID: {user.id})")
        
        # Generate OTP
        otp = self.generate_otp()
        print(f"🔢 [RESET] Generated OTP: {otp}")
        
        # Calculate expiration (10 minutes from now)
        expires_at = datetime.now() + timedelta(minutes=10)
        
        # Store OTP in database
        conn = psycopg2.connect(Config.DATABASE_URL)
        cursor = conn.cursor()
        
        try:
            # Invalidate any previous OTPs for this email
            cursor.execute('''
                UPDATE password_reset_otps 
                SET used = 1 
                WHERE email = %s AND used = 0
            ''', (email,))
            
            # Insert new OTP
            cursor.execute('''
                INSERT INTO password_reset_otps (email, otp, expires_at)
                VALUES (%s, %s, %s)
            ''', (email, otp, expires_at))
            
            conn.commit()
            print(f"✅ [RESET] OTP stored in database (expires at: {expires_at})")
            
        except psycopg2.Error as e:
            print(f"❌ [RESET] Database error: {e}")
            return False, "Failed to generate OTP. Please try again."
        finally:
            conn.close()
        
        # Send OTP via email
        print("📧 [RESET] Sending OTP email...")
        email_sent = email_service.send_otp_email(
            to_email=email,
            otp=otp,
            user_name=user.first_name
        )
        
        if email_sent:
            print(f"✅ [RESET] OTP sent successfully to: {email}")
            print("="*70 + "\n")
            return True, "OTP sent to your email. Valid for 10 minutes."
        else:
            print(f"❌ [RESET] Failed to send OTP email")
            print("="*70 + "\n")
            return False, "Failed to send OTP. Please try again."
    
    def verify_otp(self, email: str, otp: str) -> Tuple[bool, str, Optional[int]]:
        """
        Verify OTP for password reset.
        
        Args:
            email (str): User's email address
            otp (str): 6-digit OTP code
        
        Returns:
            tuple: (success: bool, message: str, user_id: Optional[int])
        
        Validation:
            - OTP must exist
            - OTP must not be expired
            - OTP must not be already used
            - OTP must match
        """
        print("\n" + "="*70)
        print("🔍 [RESET] OTP verification request")
        print(f"📧 [RESET] Email: {email}")
        print(f"🔢 [RESET] OTP: {otp}")
        
        email = email.strip().lower()
        otp = otp.strip()
        
        conn = psycopg2.connect(Config.DATABASE_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Find valid OTP
            cursor.execute('''
                SELECT id, otp, expires_at, used
                FROM password_reset_otps
                WHERE email = %s AND otp = %s AND used = 0
                ORDER BY created_at DESC
                LIMIT 1
            ''', (email, otp))
            
            row = cursor.fetchone()
            
            if not row:
                print("❌ [RESET] Invalid OTP or already used")
                print("="*70 + "\n")
                return False, "Invalid or expired OTP", None
            
            otp_id = row['id']
            expires_at = row['expires_at']
            
            # Check if expired
            if datetime.now() > expires_at:
                print(f"❌ [RESET] OTP expired (expired at: {expires_at})")
                print("="*70 + "\n")
                return False, "OTP has expired. Please request a new one.", None
            
            # Get user
            user = get_user_by_email(email)
            if not user:
                return False, "User not found", None
            
            print(f"✅ [RESET] OTP verified successfully for user_id: {user.id}")
            print("="*70 + "\n")
            
            return True, "OTP verified successfully", user.id
            
        except Exception as e:
            print(f"❌ [RESET] Error verifying OTP: {e}")
            print("="*70 + "\n")
            return False, "Failed to verify OTP", None
        finally:
            conn.close()
    
    def reset_password(self, email: str, otp: str, new_password: str) -> Tuple[bool, str]:
        """
        Reset user password after OTP verification.
        
        Args:
            email (str): User's email address
            otp (str): 6-digit OTP code
            new_password (str): New password (plain text)
        
        Returns:
            tuple: (success: bool, message: str)
        
        Process:
            1. Verify OTP
            2. Hash new password
            3. Update password in database
            4. Mark OTP as used
            5. Send confirmation email
        """
        print("\n" + "="*70)
        print("🔄 [RESET] Password reset request")
        print(f"📧 [RESET] Email: {email}")
        
        # Validate password
        if len(new_password) < 6:
            print("❌ [RESET] Password too short")
            return False, "Password must be at least 6 characters"
        
        # Verify OTP first
        success, message, user_id = self.verify_otp(email, otp)
        
        if not success:
            return False, message
        
        # Hash new password
        print("🔐 [RESET] Hashing new password...")
        password_hash = bcrypt.hashpw(
            new_password.encode('utf-8'),
            bcrypt.gensalt(Config.BCRYPT_ROUNDS)
        ).decode('utf-8')
        
        conn = psycopg2.connect(Config.DATABASE_URL)
        cursor = conn.cursor()
        
        try:
            # Update password
            print(f"💾 [RESET] Updating password for user_id: {user_id}")
            cursor.execute('''
                UPDATE users
                SET password_hash = %s
                WHERE id = %s
            ''', (password_hash, user_id))
            
            # Mark OTP as used
            cursor.execute('''
                UPDATE password_reset_otps
                SET used = 1
                WHERE email = %s AND otp = %s AND used = 0
            ''', (email, otp))
            
            conn.commit()
            print("✅ [RESET] Password updated successfully")
            
            # Get user info for confirmation email
            user = get_user_by_email(email)
            if user:
                email_service.send_password_changed_email(
                    to_email=email,
                    user_name=user.first_name
                )
            
            print("="*70 + "\n")
            return True, "Password reset successfully. You can now log in with your new password."
            
        except psycopg2.Error as e:
            print(f"❌ [RESET] Database error: {e}")
            print("="*70 + "\n")
            return False, "Failed to reset password. Please try again."
        finally:
            conn.close()
    
    def cleanup_expired_otps(self):
        """
        Clean up expired OTPs from database.
        Should be run periodically (e.g., daily cron job).
        """
        print("🧹 [RESET] Cleaning up expired OTPs...")
        
        conn = psycopg2.connect(Config.DATABASE_URL)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                DELETE FROM password_reset_otps
                WHERE expires_at < NOW()
            ''')
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            print(f"✅ [RESET] Cleaned up {deleted_count} expired OTPs")
            
        except psycopg2.Error as e:
            print(f"❌ [RESET] Cleanup error: {e}")
        finally:
            conn.close()


# Singleton instance
password_reset_manager = PasswordResetManager()
