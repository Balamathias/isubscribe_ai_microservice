from datetime import datetime
from operator import eq
import requests
import json
from typing import Dict, Any, Optional
import os
from dotenv import load_dotenv
import base64
from nanoid import generate
from supabase import Client

load_dotenv()

base_url = os.getenv('MONNIFY_BASE_URL', 'https://api.monnify.com/api/v1')
monnify_contract_code = os.getenv('MONNIFY_CONTRACT_CODE', '')


def get_user_monnify_token() -> Optional[Dict[str, Any]]:
    api_key = os.getenv('MONNIFY_API_KEY', '')
    secret_key = os.getenv('MONNIFY_SECRET_KEY', '')
    
    credentials = base64.b64encode(f"{api_key}:{secret_key}".encode()).decode()
    
    headers = {
        'Authorization': f'Basic {credentials}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(
            f"{base_url}/auth/login",
            headers=headers
        )
        
        if not response.ok:
            print('Error fetching user')
            raise Exception('Error fetching user')
            
        data = response.json()
        return {'data': data, 'status': response.status_code}
        
    except Exception as error:
        print("ERROR: ", error)
        return None


def get_reserved_account(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    token_response = get_user_monnify_token()

    token = token_response.get('data', {}).get('responseBody', {}).get('accessToken') if token_response else None
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    payload['contractCode'] = monnify_contract_code
    print(payload)
    
    try:
        response = requests.post(
            f"{base_url}/bank-transfer/reserved-accounts",
            headers=headers,
            json=payload
        )
        
        print(response.reason, response.status_code)
        print("MONNIFY RESPONSE: ", response)
        
        if not response.ok:
            print('Error fetching data')
            raise Exception('Failed to fetch reserved account')
            
        data = response.json()
        return data
        
    except Exception as error:
        print("ERROR: ", error)
        return None
    

def generate_reserved_account(request: Any) -> Dict[str, Any]:
    """
    Generate a reserved account for a user, similar to the TypeScript implementation.
    
    Args:
        request_data: Dictionary containing optional bvn and nin
    
    Returns:
        Dictionary with data and error keys
    """

    request_data = request.data if request else None
    user = request.user
    
    try:
        payload = {
            'accountReference': generate(size=24),
            'accountName': user.metadata.get('full_name', ''),
            'currencyCode': 'NGN',
            'contractCode': monnify_contract_code,
            'customerEmail': user.email,
            'customerName': user.metadata.get('full_name', ''),
            'getAllAvailableBanks': False
        }
        
        if request_data:
            if request_data.get('nin'):
                payload['nin'] = request_data.get('nin')
            if request_data.get('bvn'):
                payload['bvn'] = request_data.get('bvn')
        
        reserved_account = get_reserved_account(payload)
        
        if not reserved_account:
            return {
                'data': None,
                'error': {'message': 'Failed to create reserved account'}
            }
        
        successful = reserved_account.get('requestSuccessful', False)
        body = reserved_account.get('responseBody', {})
        
        if successful:
            account_data = {
                'account_name': body.get('accountName'),
                'account_number': body.get('accountNumber'),
                'bank_name': body.get('bankName'),
                'bank_code': body.get('bankCode'),
                'user': user.id,
                'reference': body.get('accountReference'),
                'status': body.get('status'),
                'updated_at': datetime.now().isoformat()
            }   

            supabase: Client = request.supabase_client
            
            acct_response = supabase.table('account')\
                .upsert(account_data, on_conflict='user')\
                .execute()
            
            return {'data': acct_response.data[0], 'error': None}
        else:
            error_field = "BVN" if request_data and request_data.get('bvn') else "NIN" if request_data and request_data.get('nin') else ""
            error_msg = f"Account generation failed, please double-check your {error_field}." if error_field else "Account generation failed."
            
            return {
                'data': None,
                'error': {'message': error_msg}
            }
            
    except Exception as error:
        return {
            'data': None,
            'error': {'message': str(error)}
        }
