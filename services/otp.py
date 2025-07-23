import os
import random
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from services.supabase import superbase as supabase
from services.email import send_otp_email

logger = logging.getLogger(__name__)

class OTPService:
    @staticmethod
    def generate_otp() -> str:
        """Generate a 5-digit OTP"""
        return str(random.randint(10000, 99999))
    
    @staticmethod
    def get_valid_otp_for_user(user_id: str) -> Optional[Dict[str, Any]]:
        """Get a valid, unused OTP for a user"""
        try:
            current_time = datetime.utcnow().isoformat()
            
            response = supabase.table('otp_requests').select('*').eq(
                'user_id', user_id
            ).eq(
                'used', False
            ).gt(
                'expires_at', current_time
            ).limit(1).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting valid OTP for user {user_id}: {str(e)}")
            return None
    
    @staticmethod
    def create_otp_request(user_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[Exception]]:
        """Create a new OTP request"""
        try:
            otp = OTPService.generate_otp()
            expires_at = (datetime.utcnow() + timedelta(minutes=10)).isoformat()
            
            response = supabase.table('otp_requests').insert({
                'user_id': user_id,
                'otp': otp,
                'expires_at': expires_at,
                'used': False
            }).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0], None
            
            return None, Exception("Failed to create OTP request")
            
        except Exception as e:
            logger.error(f"Error creating OTP request for user {user_id}: {str(e)}")
            return None, e
    
    @staticmethod
    def verify_otp(user_id: str, otp: str) -> bool:
        """Verify OTP and mark it as used"""
        try:
            current_time = datetime.utcnow().isoformat()
            
            response = supabase.table('otp_requests').select('*').eq(
                'user_id', user_id
            ).eq(
                'otp', otp
            ).eq(
                'used', False
            ).gt(
                'expires_at', current_time
            ).limit(1).execute()
            
            if not response.data or len(response.data) == 0:
                return False
            
            supabase.table('otp_requests').delete().eq(
                'user_id', user_id
            ).eq(
                'otp', otp
            ).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error verifying OTP for user {user_id}: {str(e)}")
            return False
    
    @staticmethod
    def cleanup_expired_otps():
        """Clean up expired OTP requests"""
        try:
            current_time = datetime.utcnow().isoformat()
            
            supabase.table('otp_requests').delete().lt(
                'expires_at', current_time
            ).execute()
            
            logger.info("Cleaned up expired OTPs")
            
        except Exception as e:
            logger.error(f"Error cleaning up expired OTPs: {str(e)}")