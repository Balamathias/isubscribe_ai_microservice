from typing import Literal, Optional
from dataclasses import dataclass
import os
import json
import upstash_redis
import requests
from dotenv import load_dotenv

load_dotenv()

redis = upstash_redis.Redis(
    url=os.getenv("UPSTASH_REDIS_REST_URL") or '',
    token=os.getenv("UPSTASH_REDIS_REST_TOKEN") or ''
)


DATA_MB_PER_NAIRA = 3.414

ISUBSCRIBE_POINTS_PER_NAIRA = 3.415

CASHBACK_VALUE = 0.01

API_KEY = os.getenv('VERIPHONE_API_KEY')
VERIPHONE_URL = 'https://api.veriphone.io/v2/verify'

def format_data_amount(amount: float | int) -> str:
    """
    Format data amount in MB or GB based on the size.
    
    Args:
        amount (float | int): Amount in MB
        
    Returns:
        str: Formatted string with appropriate unit
    """
    amount = amount * DATA_MB_PER_NAIRA

    if amount <= 1.024:
        return f"{amount:.2f}MB"
    elif 1 < amount <= 1024:
        return f"{amount:.2f}MB"
    else:
        return f"{(amount/1000):.2f}GB"


Networks = Literal['mtn', 'glo', 'airtel', '9mobile']


@dataclass
class PhoneNumberInfo:
    status: Literal['success', 'error']
    phone: str
    phone_valid: bool
    phone_type: Literal['fixed_line', 'mobile', 'unknown', 'fixed_line_or_mobile', 
                        'toll_free', 'premium_rate', 'shared_cost', 'voip']
    phone_region: str
    country: str
    country_code: str
    country_prefix: str
    international_number: str
    local_number: str
    e164: str
    carrier: str


def verify_number(phone: str) -> Optional[Networks]:
    """
    Verify phone number and return network carrier.
    
    Args:
        phone (str): Phone number to verify
        
    Returns:
        Optional[Networks]: Network carrier if found, None otherwise
    """
    try:
        cached = redis.get(f'phone:{phone}')
        
        if cached:
            data = json.loads(cached)
            carrier = data['carrier'].upper()
            return carrier.lower() if carrier in ['MTN', 'GLO', 'AIRTEL', '9MOBILE'] else None

        params = {
            'key': API_KEY,
            'phone': phone,
            'default_country': 'NG'
        }
        
        response = requests.get(VERIPHONE_URL, params=params, timeout=30)
        
        if not response.ok:
            return None
            
        if response.status_code == 402:
            print('You exhausted your limit')
            return None

        data = response.json()
        redis.set(f'phone:{phone}', json.dumps(data))
        
        carrier = data['carrier'].upper()
        return carrier.lower() if carrier in ['MTN', 'GLO', 'AIRTEL', '9MOBILE'] else None

    except Exception as error:
        import traceback
        traceback.print_exc()
        try:
            print('Error verifying phone number:', error)
            params = {
                'key': API_KEY,
                'phone': phone,
                'default_country': 'NG'
            }
            
            response = requests.get(VERIPHONE_URL, params=params)
            
            if not response.ok:
                return None
                
            if response.status_code == 402:
                print('You exhausted your limit')
                return None
                
            data = response.json()
            return data
        except Exception as error:
            print(error)
            return None
