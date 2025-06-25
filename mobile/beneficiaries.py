import json
from typing import List, Dict, Optional
from datetime import datetime
from utils import verify_number, redis

def save_beneficiary(request) -> Dict:
    """
    Save a beneficiary phone number for the current user.
    Updates frequency if phone already exists, otherwise creates new entry.
    Maintains maximum of 10 beneficiaries per user.
    """
    try:
        user = request.user
        if not user:
            return {"error": "Authentication required", "data": None}

        phone = request.data.get('phone')
        if not phone:
            return {"error": "Phone number is required", "data": None}

        network = verify_number(phone)
        if not network:
            return {"error": "Could not verify phone number", "data": None}

        supabase = request.supabase_client

        beneficiaries_response = supabase.table('beneficiaries')\
            .select('*')\
            .eq('user', user.id)\
            .order('last_used', desc=False)\
            .execute()

        if not beneficiaries_response.data:
            beneficiaries_data = []
        else:
            beneficiaries_data = beneficiaries_response.data

        if len(beneficiaries_data) >= 10:
            oldest_beneficiary_id = beneficiaries_data[0]['id']
            delete_response = supabase.table('beneficiaries')\
                .delete()\
                .eq('id', oldest_beneficiary_id)\
                .execute()

        existing_response = supabase.table('beneficiaries')\
            .select('*')\
            .eq('user', user.id)\
            .eq('phone', phone)\
            .execute()

        current_time = datetime.now().isoformat()
        
        if existing_response.data:
            existing_beneficiary = existing_response.data[0]
            new_frequency = existing_beneficiary.get('frequency', 0) + 1
            
            update_response = supabase.table('beneficiaries')\
                .update({
                    'last_used': current_time,
                    'frequency': new_frequency,
                    'network': network
                })\
                .eq('id', existing_beneficiary['id'])\
                .select('phone, last_used, frequency, network')\
                .execute()
            
            result_data = update_response.data
        else:
            insert_response = supabase.table('beneficiaries')\
                .insert({
                    'phone': phone,
                    'network': network,
                    'last_used': current_time,
                    'frequency': 1,
                    'user': user.id
                })\
                .select('phone, last_used, frequency, network')\
                .execute()
            
            result_data = insert_response.data

        cache_key = f'beneficiaries:{user.id}'
        try:
            redis.delete(cache_key)
        except Exception as e:
            print(f"Cache invalidation error: {e}")

        return {"error": None, "data": result_data}

    except Exception as e:
        print(f"Error saving beneficiary: {e}")
        return {"error": str(e), "data": None}


def get_saved_beneficiaries(request, limit: int = 5) -> Optional[List[Dict[str, str]]]:
    """
    Get saved beneficiaries for the current user, ordered by frequency (descending) then last_used (descending).
    Uses Redis cache with 30 second expiration.
    
    Returns:
        List of dicts with keys: phone, network, frequency, last_used
    """
    try:
        user = request.user
        if not user:
            return None

        supabase = request.supabase_client
        cache_key = f'beneficiaries:{user.id}'

        try:
            cached_data = redis.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            print(f"Cache retrieval error: {e}")

        response = supabase.table('beneficiaries')\
            .select('*')\
            .eq('user', user.id)\
            .order('frequency', desc=True)\
            .order('last_used', desc=True)\
            .limit(limit)\
            .execute()

        if not response.data:
            return []

        beneficiaries = response.data

        try:
            redis.set(cache_key, json.dumps(beneficiaries), ex=30)
        except Exception as e:
            print(f"Cache storage error: {e}")

        return beneficiaries

    except Exception as e:
        print(f"Error getting beneficiaries: {e}")
        return None


def process_beneficiary_from_transaction(request) -> Dict:
    """
    Automatically save beneficiary from transaction data.
    Extracts phone number from request data and determines network.
    """
    try:
        phone = request.data.get('phone')
        if not phone:
            return {"error": "Phone number not found in request", "data": None}

        # Create a mock request object for save_beneficiary
        class MockRequest:
            def __init__(self, user, supabase_client, phone):
                self.user = user
                self.supabase_client = supabase_client
                self.data = {'phone': phone}

        mock_request = MockRequest(request.user, request.supabase_client, phone)
        return save_beneficiary(mock_request)

    except Exception as e:
        print(f"Error processing beneficiary from transaction: {e}")
        return {"error": str(e), "data": None}