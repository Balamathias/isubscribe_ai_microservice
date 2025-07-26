import os
from pyparsing import C
import requests
from typing import Any, Optional, TypedDict, Literal, Union
from dotenv import load_dotenv
from nanoid import generate
from supabase import Client
from .response_code import RESPONSE_CODES
from utils import format_data_amount
from utils import CASHBACK_VALUE

from pytypes.vtpass import (
    VTPassTransactionResponse,
    MerchantVerifyResponse
)

load_dotenv()

VTPASS_API_KEY = os.getenv("VT_API_KEY")
VTPASS_SECRET_KEY = os.getenv("VT_SECRET_KEY")
VTPASS_BASE_URL = os.getenv("VT_LIVE_BASE_URL")


class BuyElectricityParams(TypedDict, total=False):
    request_id: str
    serviceID: str
    billersCode: str
    variation_code: str
    amount: float
    phone: Union[int, str]


def verify_merchant(
    type: str,
    serviceID: str,
    billersCode: str,
) -> Optional[MerchantVerifyResponse]:
    
    payload = {
        "serviceID": serviceID,
        "billersCode": billersCode,
        "type": type,
    }

    headers = {
        "api-key": VTPASS_API_KEY,
        "secret-key": VTPASS_SECRET_KEY,
        "Content-Type": "application/json",
    }

    try:
        res = requests.post(f"{VTPASS_BASE_URL}/merchant-verify", json=payload, headers=headers, timeout=50)
        print("ELECTRICITY:", res.reason, res.status_code)

        if res.status_code != 200:
            raise RuntimeError(f"Failed to verify merchant: {res.text}")

        response_data = res.json()

        print("Verify Merchant Response:", response_data)

        if not response_data:
            raise RuntimeError("Empty response from server")
            
        return response_data
    except Exception as err:
        print("Verify merchant error:", err)
        return None
    

def buy_electricity(
    request_id: str,
    serviceID: str,
    billersCode: str,
    variation_code: str,
    amount: float,
    phone: Union[int, str],
) -> Optional[VTPassTransactionResponse]:
    
    payload: BuyElectricityParams = {
        "request_id": request_id,
        "serviceID": serviceID,
        "billersCode": billersCode,
        "variation_code": variation_code,
        "amount": amount,
        "phone": phone,
    }

    headers = {
        "api-key": VTPASS_API_KEY,
        "secret-key": VTPASS_SECRET_KEY,
        "Content-Type": "application/json",
    }

    try:
        res = requests.post(f"{VTPASS_BASE_URL}/pay", json=payload, headers=headers, timeout=58)
        print("ELECTRICITY:", res.reason, res.status_code)

        if res.status_code != 200:
            raise RuntimeError(f"Failed to buy electricity: {res.text}")

        response_data = res.json()

        print("Buy Electricity Response:", response_data)

        if not response_data:
            raise RuntimeError("Empty response from server")
            
        return response_data
    except Exception as err:
        print("Buy electricity error:", err)
        return None


def process_electricity(request: Any):
    """ 
    Process electricity bill payment.
    This function handles the payment for electricity bills, including validation,
    wallet charging, and transaction history logging. Required parameters include
    ID, meter number, variation code, phone number, and amount.

    Args:
        request (Any): The request object containing user data and payment details.
    Returns:
        dict: A dictionary containing the result of the payment process, including
            success status, transaction details, and any errors encountered.
    """


    supabase: Client = request.supabase_client

    id = request.data.get('id')
    if not id:
        raise ValueError("ID is required")

    billers_code = request.data.get('billers_code')
    if not billers_code:
        raise ValueError("Meter number is required")

    variation_code = request.data.get('variation_code')
    if not variation_code:
        raise ValueError("Variation code is required")
    
    if not variation_code.lower() in ['prepaid', 'postpaid']:
        raise ValueError("Invalid variation code. Must be 'prepaid' or 'postpaid'.")

    phone = request.data.get('phone')
    if not phone:
        raise ValueError("Phone number is required")

    amount = request.data.get('amount')

    if isinstance(amount, str):
        try:
            amount = float(amount)
        except ValueError:
            raise ValueError("Invalid amount format. Must be a number.")
        
    if not amount:
        raise ValueError("Amount is required")
    if amount < 100:
        raise ValueError(f'Electricity amount below {amount:.2f} not allowed.')
    
    COMMISSION = 0.1  # 10% commission

    amount = (amount * COMMISSION) + amount ### Add 10% commission to original amount.

    request_id = generate(size=24)

    payment_method: str = request.data.get('payment_method', 'wallet')

    if payment_method.lower() not in ['wallet', 'cashback']:
        raise Exception('Unknown payment method selected.')

    cashback_balance = 0
    balance = 0

    try:
        wallet = supabase.table('wallet').select('user, cashback_balance, balance')\
            .eq('user', request.user.id).single().execute()
        if not wallet.data:
            raise ValueError("Wallet not found")
            
        cashback_balance = wallet.data.get('cashback_balance', 0)
        balance = wallet.data.get('balance', 0)

    except Exception as e:
        raise Exception(f"Failed to fetch wallet: {str(e)}")

    def charge_wallet(method: str = 'wallet', amount: int | float = 0, refund: bool = False):
        if not isinstance(amount, (int, float)) or amount <= 0:
            return {'error': 'Invalid amount'}

        if method == 'cashback' and amount > 1000:
            raise ValueError(f'You cannot purchase a plan above N 1,000 with Data Bonus at a time.')
            
        return_cashback = (amount * CASHBACK_VALUE)
            
        try:
            supabase.rpc('update_wallet_balance', {
                'user_id': str(request.user.id),
                'amount': -float(amount) if refund else float(amount),
                'charge_from': method
            }).execute()
            
            supabase.rpc('update_cashback_balance', {
                'user_id': str(request.user.id),
                'cashback': -return_cashback if refund else return_cashback
            }).execute()
                
        except Exception as e:
            print("RPC Error: ", e)
            return {'error': str(e)}
        
    if payment_method == 'wallet' and balance < amount:
        raise ValueError(f"Insufficient wallet balance. Required: {amount}, Available: {balance}")
    
    if payment_method == 'cashback' and cashback_balance < amount:
        raise ValueError(f"Insufficient cashback balance. Required: {amount}, Available: {cashback_balance}")
    
    electricity_services = supabase.table('electricity')\
        .select('*')\
        .eq('id', id)\
        .single()\
        .execute()

    if not electricity_services.data:
        raise ValueError("Electricity service not found")

    service_id = electricity_services.data.get('service_id', '')

    cw = charge_wallet(payment_method, amount=amount)

    if cw and cw.get('error'):
        raise Exception(cw.get('error'))

    response = buy_electricity(
        request_id=request_id,
        serviceID=service_id,
        billersCode=billers_code,
        variation_code=variation_code,
        amount=amount,
        phone=phone
    )

    if not response:
        raise Exception('No response was received from the server')

    code = response.get('code')

    if not code:
        raise Exception('Invalid response format: missing code')

    content = response.get('content', {})
    transactions = content.get('transactions', {})
    commission = transactions.get('commission', 0)

    payload = {
        'title': 'Electricity Bill Payment',
        'status': 'success',
        'description': f'Electricity bill paid successfully for meter {billers_code}',
        'user': request.user.id,
        'amount': amount,
        'provider': 'vtpass',
        'type': 'meter_topup',
        'commission': (commission + (amount * COMMISSION)),
        'balance_before': balance,
        'balance_after': balance - amount,
        'source': request.data.get('source', 'mobile'),
    }

    bonus_cashback = amount * CASHBACK_VALUE

    def format_token(token: str) -> str:
        if not token:
            return 'N/A'
        return f"{token[:4]}-{token[4:8]}-{token[8:12]}-{token[12:16]}-{token[16:]}" if len(token) >= 20 else token

    if code == '000':

        token = response.get('token') or response.get('MainToken') or response.get('mainToken') or response.get('Token', '') or response.get('purchased_code', '')

        if token and ':' in token:
            token = ''.join(filter(str.isdigit, token.split(':')[-1].strip()))
        elif token:
            token = ''.join(filter(str.isdigit, token))
        
        payload['meta_data'] = { 
            'cashback_bonus': bonus_cashback,
            'meter_number': billers_code,
            'service': service_id,
            'variation_code': variation_code,
            'phone': phone,
            'token': token,
            'formatted_token': format_token(token)
        }

        history_response = supabase.table('history')\
            .insert(payload)\
            .execute()
        
        if not history_response.data:
            raise Exception("Failed to insert transaction history")

        payload['title'] = 'Cashback Bonus'
        payload['description'] = f'You have successfully received a cashback bonus of ₦{bonus_cashback:.2f}.'
        payload['amount'] = bonus_cashback
        payload['type'] = 'cashback'
        payload['meta_data'] = { 
            'cashback_bonus': bonus_cashback,
            'meter_number': billers_code,
            'service': service_id,
            'variation_code': variation_code,
            'phone': phone
        }

        cashback_response = supabase.table('history')\
            .insert(payload)\
            .execute()
        
        if not cashback_response.data:
            raise Exception("Failed to insert cashback history")
        
        return {
            'success': True,
            'data': {
                **history_response.data[0],
                'cashback_bonus': bonus_cashback,
                'token': token,
                'formatted_token': format_token(token)
            }
        }

    elif code == '099':
        
        payload['status'] = 'pending'
        payload['description'] = 'Transaction Pending.'

        history_response = supabase.table('history')\
            .insert(payload)\
            .execute()
        
        if not history_response.data:
            raise Exception("Failed to insert pending transaction history")
        
        return {
            'success': False,
            'data': history_response.data[0],
            'status': 'pending',
        }
    
    else:
        cw = charge_wallet(
            payment_method,
            amount=amount,
            refund=True
        )

        if cw and cw.get('error'):
            raise Exception(cw.get('error'))
        
        payload['status'] = 'failed'
        payload['description'] = RESPONSE_CODES.get(code, {}).get('message', 'Unknown error')
        payload['balance_before'] = balance
        payload['balance_after'] = balance

        history_response = supabase.table('history')\
            .insert(payload)\
            .execute()
        
        if not history_response.data:
            raise Exception("Failed to insert failed transaction history")
        
        return {
            'success': False,
            'data': history_response.data[0],
            'status': 'failed'
        }