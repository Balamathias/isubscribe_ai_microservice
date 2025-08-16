import os
from typing import Literal, Optional, Union, Any
import requests
from nanoid import generate
from supabase import Client
from dotenv import load_dotenv

from mobile.airtime import VTPASS_API_KEY, VTPASS_BASE_URL, VTPASS_SECRET_KEY
from pytypes.vtpass import VTPassTransactionResponse, MerchantVerifyResponse
from mobile.response_code import RESPONSE_CODES
from utils import CASHBACK_VALUE, format_data_amount

load_dotenv()


def verify_education_merchant(
    serviceID: Literal['jamb', 'waec'],
    billersCode: str,
    variation_code: str,
) -> Optional[MerchantVerifyResponse]:
    """
    Verify education service merchant details.
    Only JAMB requires verification (Profile ID), WAEC doesn't need verification.
    """
    
    if serviceID == 'waec':
        return {
            "code": "000",
            "content": {
                "Customer_Name": "WAEC Student",
                "Address": "N/A",
                "MeterNumber": "N/A", 
                "Min_Purchase_Amount": 900,
                "Outstanding": 0,
                "Customer_Arrears": None,
                "Meter_Type": "N/A",
                "WrongBillersCode": False,
                "commission_details": {
                    "amount": "10.22",
                    "rate": "1.50", 
                    "rate_type": "percent",
                    "computation_type": "default"
                }
            }
        }
    
    payload = {
        "serviceID": serviceID,
        "billersCode": billersCode,
        "type": variation_code,
    }

    headers = {
        "api-key": VTPASS_API_KEY,
        "secret-key": VTPASS_SECRET_KEY,
        "Content-Type": "application/json",
    }

    try:
        res = requests.post(f"{VTPASS_BASE_URL}/merchant-verify", json=payload, headers=headers, timeout=50)
        print("EDUCATION VERIFY:", res.reason, res.status_code)

        if res.status_code != 200:
            raise RuntimeError(f"Failed to verify education merchant: {res.text}")

        response_data = res.json()
        print("Verify Education Merchant Response:", response_data)

        if not response_data:
            raise RuntimeError("Empty response from server")
            
        return response_data
    except Exception as err:
        print("Verify education merchant error:", err)
        return None


def buy_education(
    request_id: str,
    serviceID: str,
    variation_code: Literal['de', 'utme', 'waecdirect'],
    phone: Union[int, str],
    quantity: Optional[int],
    amount: Optional[float],
    billersCode: Optional[str] = None
) -> Optional[VTPassTransactionResponse]:
    
    payload = {
        "request_id": request_id,
        "serviceID": serviceID,
        "variation_code": variation_code,
        "amount": amount,
        "phone": phone,
        "quantity": quantity,
        "billersCode": billersCode
    }

    headers = {
        "api-key": VTPASS_API_KEY,
        "secret-key": VTPASS_SECRET_KEY,
        "Content-Type": "application/json",
    }

    try:
        res = requests.post(f"{VTPASS_BASE_URL}/pay", json=payload, headers=headers, timeout=58)
        print("EDUCATION:", res.reason, res.status_code)

        if res.status_code != 200:
            raise RuntimeError(f"Failed to buy education: {res.text}")

        response_data = res.json()

        print("Buy Education Response:", response_data)

        if not response_data:
            raise RuntimeError("Empty response from server")
            
        return response_data
    except Exception as err:
        print("Buy education error:", err)
        return None


def process_education(request: Any):
    """
    Process education service payments (JAMB, WAEC, Direct Entry).
    This function handles payment for education services including validation,
    wallet charging, and transaction history logging.
    
    Different services have different requirements:
    - JAMB (jamb): Requires Profile ID verification, returns Pin
    - WAEC (waec): No verification needed, returns cards with Serial and Pin  
    - Direct Entry (de): Similar to JAMB, requires Profile ID verification
    
    Args:
        request (Any): The request object containing user data and payment details.
    Returns:
        dict: A dictionary containing the result of the payment process.
    """
    
    supabase: Client = request.supabase_client
    
    service_type = request.data.get('service_type')  # 'jamb', 'waec', 'de'
    if not service_type:
        raise ValueError("Service type is required (jamb, waec, or de)")
    
    if service_type not in ['jamb', 'waec', 'de']:
        raise ValueError("Invalid service type. Must be 'jamb', 'waec', or 'de'")
    
    variation_code = request.data.get('variation_code')
    if not variation_code:
        raise ValueError("Variation code is required")
    
    phone = request.data.get('phone')
    if not phone:
        raise ValueError("Phone number is required")
    
    quantity = request.data.get('quantity', 1)
    try:
        quantity = int(quantity)
    except (ValueError, TypeError):
        quantity = 1
    
    if quantity < 1 or quantity > 10:
        raise ValueError("Quantity must be between 1 and 10")
    
    billers_code = request.data.get('billers_code') or request.data.get('profile_id')
    
    if service_type in ['jamb', 'de'] and not billers_code:
        raise ValueError("Profile ID is required for JAMB and Direct Entry services")
    
    service_query = supabase.table('education')\
        .select('*')\
        .eq('service_type', service_type)\
        .eq('variation_code', variation_code)\
        .single()\
        .execute()
    
    if not service_query.data:
        raise ValueError(f"Education service not found for {service_type} with variation {variation_code}")
    
    service_config = service_query.data
    service_id = service_config.get('service_id', service_type)
    base_amount = float(service_config.get('price', 0))
    commission_rate = float(service_config.get('commission_rate', 0.1))  # 10% default
    
    if base_amount <= 0:
        raise ValueError("Invalid service price configuration")
    
    total_amount = (base_amount * quantity) * (1 + commission_rate)
    
    payment_method = request.data.get('payment_method', 'wallet')
    if payment_method.lower() not in ['wallet', 'cashback']:
        raise ValueError('Invalid payment method. Use "wallet" or "cashback"')
    
    try:
        wallet = supabase.table('wallet').select('user, cashback_balance, balance')\
            .eq('user', request.user.id).single().execute()
        if not wallet.data:
            raise ValueError("Wallet not found")
            
        cashback_balance = wallet.data.get('cashback_balance', 0)
        balance = wallet.data.get('balance', 0)
    except Exception as e:
        raise Exception(f"Failed to fetch wallet: {str(e)}")
    
    if payment_method == 'wallet' and balance < total_amount:
        raise ValueError(f"Insufficient wallet balance. Required: ₦{total_amount:.2f}, Available: ₦{balance:.2f}")
    
    if payment_method == 'cashback':
        if total_amount > 1000:
            raise ValueError('You cannot purchase education services above ₦1,000 with Data Bonus')
        if cashback_balance < total_amount:
            raise ValueError(f"Insufficient cashback balance. Required: ₦{total_amount:.2f}, Available: ₦{cashback_balance:.2f}")
    
    request_id = generate(size=24)
    
    if service_type in ['jamb', 'de'] and billers_code:
        verification = verify_education_merchant(
            serviceID=service_id,
            billersCode=billers_code,
            variation_code=variation_code
        )
        
        if not verification or verification.get('code') != '000':
            raise ValueError("Failed to verify Profile ID. Please check the Profile ID and try again.")
    
    def charge_wallet(method: str = 'wallet', amount: float = 0, refund: bool = False):
        if not isinstance(amount, (int, float)) or amount <= 0:
            return {'error': 'Invalid amount'}
            
        return_cashback = amount * CASHBACK_VALUE
            
        try:
            supabase.rpc('update_wallet_balance', {
                'user_id': str(request.user.id),
                'amount': -float(amount) if not refund else float(amount),
                'charge_from': method
            }).execute()
            
            supabase.rpc('update_cashback_balance', {
                'user_id': str(request.user.id),
                'cashback': return_cashback if not refund else -return_cashback
            }).execute()
                
        except Exception as e:
            print("RPC Error: ", e)
            return {'error': str(e)}
        
        return {'success': True}
    
    response = buy_education(
        request_id=request_id,
        serviceID=service_id,
        variation_code=variation_code,
        phone=phone,
        quantity=quantity,
        amount=total_amount,
        billersCode=billers_code
    )
    
    if not response:
        raise Exception('No response received from education service provider')
    
    code = response.get('code')
    if not code:
        raise Exception('Invalid response format: missing code')
    
    content = response.get('content', {})
    transactions = content.get('transactions', {})
    commission = transactions.get('commission', 0)
    
    service_names = {
        'jamb': 'JAMB PIN Purchase',
        'waec': 'WAEC Result Checker',
        'de': 'Direct Entry PIN Purchase'
    }
    
    payload = {
        'title': service_names.get(service_type, 'Education Service'),
        'status': 'success',
        'description': f'{service_names.get(service_type, "Education Service")} for {phone}',
        'user': request.user.id,
        'amount': total_amount,
        'provider': 'vtpass',
        'type': 'education',
        'commission': commission + (total_amount * commission_rate),
        'balance_before': balance,
        'balance_after': balance - total_amount,
        'source': request.data.get('source', 'mobile'),
        'meta_data': {
            'service_type': service_type,
            'variation_code': variation_code,
            'quantity': quantity,
            'phone': phone,
            'profile_id': billers_code,
        }
    }
    
    bonus_cashback = total_amount * CASHBACK_VALUE

    charge_result = charge_wallet(payment_method, amount=total_amount)
    if charge_result.get('error'):
        raise Exception(charge_result.get('error'))
    
    payload['status'] = 'pending'

    tx_response = supabase.table('history')\
        .insert(payload)\
        .execute()
    
    if code == '000':
        pins = []
        cards = []

        payload['status'] = 'success'
        payload['description'] = f"{service_names.get(service_type, 'Education Service')} for {phone} completed successfully"
        
        if response.get('Pin'):
            pin_text = response.get('Pin', '')
            if ':' in pin_text:
                pin_value = pin_text.split(':')[-1].strip()
                pins.append(pin_value)
        
        if response.get('cards'):
            cards = response.get('cards', [])
        
        purchased_code = response.get('purchased_code', '')
        if purchased_code and not pins and not cards:
            if service_type in ['jamb', 'de']:
                # Format: "Pin : 3678251321392432"
                if ':' in purchased_code:
                    pin_value = purchased_code.split(':')[-1].strip()
                    pins.append(pin_value)
            elif service_type == 'waec':
                # Format: "Serial No:WRN123456790, pin: 098765432112"
                if 'Serial' in purchased_code and 'pin:' in purchased_code:
                    parts = purchased_code.split(',')
                    serial = ''
                    pin = ''
                    for part in parts:
                        if 'Serial' in part and ':' in part:
                            serial = part.split(':')[-1].strip()
                        elif 'pin:' in part:
                            pin = part.split(':')[-1].strip()
                    if serial and pin:
                        cards.append({"Serial": serial, "Pin": pin})
        
        # Update metadata with results
        payload['meta_data'].update({
            'data_bonus': bonus_cashback,
            'pins': pins,
            'cards': cards,
            'purchased_code': purchased_code
        })
        
        # Insert main transaction
        history_response = supabase.table('history')\
            .update(payload)\
            .eq('id', tx_response.data[0]['id'])\
            .execute()
        
        if not history_response.data:
            raise Exception("Failed to insert transaction history")
        
        # Insert cashback bonus transaction
        cashback_payload = {
            'title': 'Isubscribe Points',
            'description': f'Isubscribe Points of {format_data_amount(bonus_cashback)} for education service purchase',
            'user': request.user.id,
            'amount': bonus_cashback,
            'provider': 'vtpass',
            'type': 'cashback',
            'status': 'success',
            'balance_before': balance,
            'balance_after': balance - total_amount,
            'meta_data': {
                'source': 'education_purchase',
                'original_amount': total_amount,
                'service_type': service_type
            }
        }
        
        supabase.table('history').insert(cashback_payload).execute()
        
        return {
            'success': True,
            'data': {
                **history_response.data[0],
                'data_bonus': bonus_cashback,
                'pins': pins,
                'cards': cards
            }
        }
    
    elif code == '099':
        charge_result = charge_wallet(payment_method, amount=total_amount, refund=True)
        if charge_result.get('error'):
            raise Exception(charge_result.get('error'))
        
        payload['status'] = 'pending'
        payload['description'] = 'Education service purchase is pending'

        history_response = supabase.table('history').update(payload).eq('id', tx_response.data[0]['id']).execute()

        if not history_response.data:
            raise Exception("Failed to insert pending transaction history")
        
        return {
            'success': False,
            'status': 'pending',
            'data': history_response.data[0]
        }
    
    else:

        charge_result = charge_wallet(payment_method, amount=total_amount, refund=True)
        if charge_result.get('error'):
            raise Exception(charge_result.get('error'))
        
        payload['status'] = 'failed'
        payload['description'] = RESPONSE_CODES.get(code, {}).get('message', 'Education service purchase failed')
        payload['balance_after'] = balance

        history_response = supabase.table('history').update(payload).eq('id', tx_response.data[0]['id']).execute()

        if not history_response.data:
            raise Exception("Failed to insert failed transaction history")
        
        return {
            'success': False,
            'status': 'failed',
            'data': history_response.data[0]
        }
    