import logging
from typing import Optional, Tuple
from mobile.bcrypt import hash_pin
from services.supabase import superbase as supabase

logger = logging.getLogger(__name__)

class PINService:

    @staticmethod
    def verify_pin(user_id: str, pin: str) -> bool:
        """Verify a user's PIN"""
        try:
            hashed_pin = hash_pin(pin)
            
            response = supabase.table('profile').select('pin').eq(
                'id', user_id
            ).single().execute()
            
            if response.data and response.data.get('pin') == hashed_pin:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error verifying PIN for user {user_id}: {str(e)}")
            return False
    
    @staticmethod
    def update_pin(user_id: str, new_pin: str) -> Tuple[bool, Optional[Exception]]:
        """Update a user's PIN"""
        try:
            hashed_pin = hash_pin(new_pin)
            
            response = supabase.table('profile').update({
                'pin': hashed_pin
            }).eq('id', user_id).execute()
            
            if response.data:
                logger.info(f"PIN updated successfully for user {user_id}")
                return True, None
            
            return False, Exception("Failed to update PIN")
            
        except Exception as e:
            logger.error(f"Error updating PIN for user {user_id}: {str(e)}")
            return False, e