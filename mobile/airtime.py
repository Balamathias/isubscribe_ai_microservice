import os
import requests
from typing import Any, Optional, TypedDict, Literal, Union
from dotenv import load_dotenv
from nanoid import generate
from supabase import Client

from .response_code import RESPONSE_CODES
from utils import format_data_amount

from pytypes.vtpass import (
    VTPassTransactionResponse
)

load_dotenv()

VTPASS_API_KEY = os.getenv("VT_API_KEY")
VTPASS_SECRET_KEY = os.getenv("VT_SECRET_KEY")
VTPASS_BASE_URL = os.getenv("VT_LIVE_BASE_URL")


class BuyAirtimeParams(TypedDict, total=False):
    request_id: str
    serviceID: Literal["glo", "mtn", "airtel", "etisalat"]
    phone: Union[int, str]
    amount: float


def buy_airtime(
    request_id: str,
    serviceID: Literal["glo", "mtn", "airtel", "etisalat"],
    phone: Union[int, str],
    amount: Optional[float] = None,
) -> Optional[VTPassTransactionResponse]:
    
    payload: BuyAirtimeParams = {
        "request_id": request_id,
        "serviceID": serviceID,
        "phone": phone,
    }

    if amount is not None:
        payload["amount"] = amount

    headers = {
        "api-key": VTPASS_API_KEY,
        "secret-key": VTPASS_SECRET_KEY,
        "Content-Type": "application/json",
    }

    try:
        res = requests.post(f"{VTPASS_BASE_URL}/pay", json=payload, headers=headers, timeout=30)
        print("AIRTSTATS:", res.reason, res.status_code)

        if res.status_code != 200:
            raise RuntimeError(f"Failed to buy airtime: {res.text}")

        response_data = res.json()
        if not response_data:
            raise RuntimeError("Empty response from server")
            
        return response_data
    except Exception as err:
        print("Buy airtime error:", err)
        return None
    

def process_airtime(request: Any):

    from utils import CASHBACK_VALUE

    supabase: Client = request.supabase_client

    network = request.data.get('network')
    if not network:
        raise ValueError("Network is required")
    network = 'etisalat' if network == '9mobile' else network

    phone = request.data.get('phone')
    if not phone:
        raise ValueError("Phone number is required")

    amount = request.data.get('amount')
    if not amount:
        raise ValueError("Amount is required")
    if amount < 25:
        raise ValueError(f'Airtime amount below {amount:.2f} not allowed.')

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
        print("SUP Wal EXC", e)
        raise Exception(f"Failed to fetch wallet: {str(e)}")

    def charge_wallet(method: str = 'wallet', refund: bool = False):
        return_cashback = (amount * CASHBACK_VALUE)
        balance_to_check = balance if method == 'wallet' else cashback_balance
        balance_type = 'wallet' if method == 'wallet' else 'cashback'
        
        if not refund and balance_to_check < amount:
            return {
                'error': f'Insufficient {balance_type} balance'
            }
        
        try:
            rpc_response = supabase.rpc('charge_wallet', {
                'user_id': str(request.user.id),
                'amount': -float(amount) if refund else float(amount),
                'cashback': -return_cashback if refund else return_cashback,
                'charge_from': method,
            }).execute()
            
            if method == 'wallet':
                print(f"RPC Result: ", rpc_response)
                            
        except Exception as e:
            if method == 'wallet':
                print("RPC Error: ", e)
            message = e.args[0].get('message', str(e)) if isinstance(e.args[0], dict) and 'message' in e.args[0] else str(e)
            return {'error': message}
    
    # if payment_method == 'wallet' and balance < amount:
    #     raise ValueError(f"Insufficient wallet balance. Required: {amount}, Available: {balance}")
    
    # if payment_method == 'cashback' and cashback_balance < amount:
    #     raise ValueError(f"Insufficient cashback balance. Required: {amount}, Available: {cashback_balance}")

    cw = charge_wallet(payment_method)

    if cw and cw.get('error'):
        raise Exception(cw.get('error'))
            
    response = buy_airtime(
        request_id=request_id,
        amount=amount,
        phone=phone,
        serviceID=network
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
        'title': 'Airtime Subscription',
        'status': 'success',
        'description': f'Airtime topped up successfully for {phone}',
        'user': request.user.id,
        'amount': amount,
        'provider': 'vtpass',
        'type': 'airtime_topup',
        'commission': commission,
        'balance_before': balance,
        'balance_after': balance - amount,
        'source': request.data.get('source', 'mobile'),
    }

    bonus_cashback = amount * CASHBACK_VALUE

    if code == '000':

        history_response = supabase.table('history')\
            .insert(payload)\
            .execute()
        
        if not history_response.data:
            raise Exception("Failed to insert transaction history")

        payload['title'] = 'Data Bonus'
        payload['description'] = f'You have successfully received a data bonus of {format_data_amount(bonus_cashback)}.'
        payload['amount'] = bonus_cashback
        payload['type'] = 'cashback'
        payload['meta_data'] = { 
            'data_bonus': format_data_amount(bonus_cashback),
            'phone': phone,
            'network': network
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
                'data_bonus': format_data_amount(bonus_cashback)
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
            'data': history_response.data[0]
        }
    
    else:
        cw = charge_wallet(payment_method, refund=True)
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
            'data': history_response.data[0]
        }