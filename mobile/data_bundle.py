import os

from typing import Any, Optional, TypedDict, Literal, Union
from dotenv import load_dotenv
from nanoid import generate
from supabase import Client
import requests

from utils import format_data_amount

from pytypes.data_bundle import Payload as SuperPayload, ResponseData, GsubPayload, GsubResponse
from pytypes.vtpass import VTPassTransactionResponse, VTPassTransactionRequest

from .response_code import GSUB_RESPONSE_CODES, RESPONSE_CODES

load_dotenv()

N3T_TOKEN = os.getenv("N3TDATA_TOKEN")
N3T_BASE_URL = 'https://n3tdata.com/api'

VTPASS_API_KEY = os.getenv("VT_API_KEY")
VTPASS_SECRET_KEY = os.getenv("VT_SECRET_KEY")
VTPASS_BASE_URL = os.getenv("VT_LIVE_BASE_URL")

def get_regular_bundle(
    request_id: str,
    serviceID: Literal['mtn-data', 'glo-data', 'airtel-data', '9mobile-data'],
    phone: Union[int, str],
    variation_code: str,
    amount: Optional[float] = None,
) -> Optional[VTPassTransactionResponse]:
    
    payload: VTPassTransactionRequest = {
        "request_id": request_id,
        "serviceID": serviceID,
        "billersCode": phone,
        "variation_code": variation_code,
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
        print("DATABSTATS:", res.reason, res.status_code)

        if res.status_code != 200:
            raise RuntimeError(f"Failed to buy data bundle: {res.text}")

        response_data = res.json()
        if not response_data:
            raise RuntimeError("Empty response from server")
            
        return response_data
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"HTTP error occurred: {e.response.status_code} - {e.response.reason}")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Request failed: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error: {str(e)}")



def get_super_bundle(payload: SuperPayload) -> Union[ResponseData, None]:
    headers = {
        'Authorization': f'Token {N3T_TOKEN}',
        'Content-Type': 'application/json',
    }

    mapped = {
        'mtn': 1,
        'airtel': 2,
        'glo': 3,
        '9mobile': 4
    }
    
    try:
        req_body = payload.copy()
        req_body.pop('request_id')
        req_body['request-id'] = payload['request_id']
        req_body['network'] = mapped[payload.get('network')]

        res = requests.post(f"{N3T_BASE_URL}/data", json=req_body, headers=headers, timeout=30)
        res.raise_for_status()
        
        data = res.json()

        print("\n\nResponse Data: ", data)
        return data
        
    except requests.exceptions.HTTPError as e:
        import traceback
        traceback.print_exc()
        raise Exception(f"HTTP error occurred: {e.response.status_code} - {e.response.reason}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Request failed: {str(e)}")
    except Exception as e:
        raise Exception(f"Unexpected error: {str(e)}")
    

def get_best_bundle(payload: GsubPayload) -> Union[GsubResponse, None]:
    headers = {
        'Authorization': f'Bearer {os.getenv("GSUB_API_KEY")}',
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    
    url_params = {
        'plan': payload['plan'],
        'phone': payload['phone'],
        'amount': '',
        'api': os.getenv("GSUB_API_KEY"),
        'requestID': payload['requestID'],
        'serviceID': payload['serviceID']
    }
    
    try:
        res = requests.post(
            'https://api.gsubz.com/api/pay/',
            headers=headers,
            data=url_params,
            timeout=30
        )
        res.raise_for_status()
        
        data = res.json()
        if not data:
            return None
            
        return {
            'code': data.get('code', 0),
            'status': data.get('status', 'failed'),
            'transactionID': data.get('transactionID', ''),
            'amount': float(data.get('amount', 0)),
            'phone': data.get('phone', ''),
            'serviceID': data.get('serviceID', ''),
            'amountPaid': float(data.get('amountPaid', 0)),
            'initialBalance': float(data.get('initialBalance', 0)),
            'finalBalance': float(data.get('finalBalance', 0)),
            'date': data.get('date', ''),
            'api_response': data.get('api_response', '')
        }
        
    except requests.exceptions.HTTPError as e:
        raise Exception(f"HTTP error occurred: {e.response.status_code} - {e.response.reason}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Request failed: {str(e)}")
    except Exception as e:
        raise Exception(f"Unexpected error: {str(e)}")


def process_data_bundle(request: Any):

    """
    Function to handle data processing for all categories.
    request.data requires `plan_id, category, phone and payment_method`.
    """

    supabase: Client = request.supabase_client
    from utils import CASHBACK_VALUE

    phone = request.data.get('phone')
    if not phone:
        raise ValueError("Phone number is required")

    category = request.data.get('category')
    if not category:
        raise ValueError("Data category is required")

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

    def charge_wallet(method: str = 'wallet', amount: int = 0, refund: bool = False):
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
            message = e.args[0].get('message', str(e)) if isinstance(e.args[0], dict) and 'message' in e.args[0] else str(e)
            return {'error': message}
        
    payload = {
        'title': 'Data Subscription',
        'status': 'success',
        'description': f'Data topped up successfully for {phone}.',
        'user': request.user.id,
        'amount': 0,
        'provider': 'gsub',
        'type': 'data_topup',
        'commission': 0,
        'balance_before': balance,
        'balance_after': 0,
        'source': request.data.get('source', 'mobile'),
    }

    if category == 'best':
        plan_id = request.data.get('plan_id')

        if not plan_id:
            raise ValueError('Plan ID as plan_id is required.')
        
        data_plan = (supabase.table('gsub')\
            .select('*')\
            .eq('id', plan_id).single().execute()).data
        
        amount = data_plan.get('price', 0) + data_plan.get('commission', 0)

        cw = charge_wallet(
            payment_method,
            amount=amount,
        )

        if cw and cw.get('error'):
            raise Exception(cw.get('error'))
        
        response = get_best_bundle({
            'phone': phone,
            'serviceID': data_plan.get('service_id', ''),
            'plan': data_plan.get('value', ''),
            'requestID': generate(size=24),
        })

        if not response:
            raise Exception('No response was returned from the server.')
        
        if response.get('status') in ['failed', 'TRANSACTION_FAILED']:
            cw = charge_wallet(
                payment_method,
                amount=amount,
                refund=True
            )

            if cw and cw.get('error'):
                raise RuntimeError(cw.get('error'))

            payload['amount'] = amount
            payload['description'] = GSUB_RESPONSE_CODES.get(str(response.get('code', None)), {}).get('message', f'Data subscription for {phone} failed.')
            payload['balance_after'] = balance if payment_method == 'wallet' else None
            payload['status'] = 'failed'

            history_response = supabase.table('history')\
                .insert(payload)\
                .execute()
            
            if not history_response.data:
                raise Exception("Failed to insert pending transaction history")
            
            return {
                'success': False,
                'data': {
                    **data_plan,
                    **history_response.data[0],
                    'amount': amount
                },
            }
        
        if response.get('code') == 200:
            payload['amount'] = amount
            payload['description'] = f'You have successfully topped up {data_plan.get('quantity')} for {phone}.'
            payload['balance_after'] = (balance - amount) if payment_method == 'wallet' else None
            payload['transaction_id'] = response.get('transactionID', None)
            payload['commission'] = data_plan.get('commission')

            history_response = supabase.table('history')\
                .insert(payload)\
                .execute()
            
            if not history_response.data:
                raise Exception("Failed to insert transaction history")
            
            return_cashback = (amount * CASHBACK_VALUE)

            payload['title'] = 'Data Bonus'
            payload['description'] = f'You have successfully received a data bonus of {format_data_amount(return_cashback)}.'
            payload['amount'] = return_cashback
            payload['type'] = 'cashback'
            payload['meta_data'] = {
                    **data_plan,
                    'data_bonus': format_data_amount(return_cashback),
                    'phone': phone,
                    'network': data_plan.get('network')
                }

            cashback_response = supabase.table('history')\
                .insert(payload)\
                .execute()
            
            if not cashback_response.data:
                raise Exception("Failed to insert cashback history")
            
            return {
                'success': True,
                'data': {
                    **data_plan,
                    **history_response.data[0],
                    'amount': amount
                },
            }
        
        if response.get('status') == 'reversed':
            payload['amount'] = amount
            payload['description'] = f'Data plan {data_plan.get("quantity")} reversed for {phone}.'
            payload['balance_after'] = balance
            payload['status'] = 'reversed'

            history_response = supabase.table('history')\
                .insert(payload)\
                .execute()
            
            if not history_response.data:
                raise Exception("Failed to insert reversed transaction history")
            
            return {
                'success': False,
                'data': {
                    **data_plan,
                    **history_response.data[0],
                    'amount': amount,
                    'data_bonus': format_data_amount(data_plan.get('cash_back') or return_cashback),
                },
            }
        
        else:
            payload['amount'] = amount
            payload['description'] = f'Data plan {data_plan.get('quantity')} pending for {phone}.'
            payload['balance_after'] = (balance - amount) if payment_method == 'wallet' else None
            payload['status'] = 'pending'

            history_response = supabase.table('history')\
                .insert(payload)\
                .execute()
            
            if not history_response.data:
                raise Exception("Failed to insert transaction history")
            
            return {
                'success': False,
                'data': {
                    **data_plan,
                    **history_response.data[0],
                    'amount': amount
                },
                'status': 'pending'
            }
        

    if category == 'super':
        plan_id = request.data.get('plan_id')

        if not plan_id:
            raise ValueError('Plan ID as plan_id is required.')
        
        data_plan = (supabase.table('n3t')\
            .select('*')\
            .eq('id', plan_id).single().execute()).data
        
        amount = data_plan.get('price', 0) ## Here be dragons, the price of this one has commission added to it from the database already.
        print("Amount: ", amount)

        if amount > balance and payment_method == 'wallet':
            raise ValueError('Insufficient wallet balance for the selected data plan.')
        if amount > cashback_balance and payment_method == 'cashback':
            raise ValueError('Insufficient cashback balance for the selected data plan.')
        
        cw = charge_wallet(
                payment_method,
                amount=amount,
            )

        if cw and cw.get('error'):
            raise Exception(cw.get('error'))
        
        response = get_super_bundle({
            'bypass': False,
            'request_id': f'Data_{generate(size=32)}',
            'data_plan': data_plan.get('value'),
            'network': data_plan.get('network'),
            'phone': phone
        })

        if not response:
            raise RuntimeError('Server failed to return a response.')

        if response and response.get('status') in ['success', 'pending']:

            payload['amount'] = amount
            payload['description'] = f'You have successfully topped up {data_plan.get('quantity')} for {phone}.'
            payload['balance_after'] = (balance - amount) if payment_method == 'wallet' else None
            payload['transaction_id'] = response.get('request-id', None)
            payload['commission'] = data_plan.get('commission')

            if response.get('status') == 'pending':
                payload['description'] = f'Data plan for {phone} is pending.'

            history_response = supabase.table('history')\
                .insert(payload)\
                .execute()
            
            if not history_response.data:
                raise Exception("Failed to insert transaction history")
            
            return_cashback = (amount * CASHBACK_VALUE)

            if response.get('status') == 'success':

                payload['title'] = 'Data Bonus'
                payload['description'] = f'You have successfully received a data bonus of {format_data_amount(return_cashback)}.'
                payload['amount'] = return_cashback
                payload['type'] = 'cashback'
                payload['meta_data'] = {
                    **data_plan,
                    'data_bonus': format_data_amount(return_cashback),
                    'phone': phone,
                    'network': data_plan.get('network')
                }

                cashback_response = supabase.table('history')\
                    .insert(payload)\
                    .execute()
                
                if not cashback_response.data:
                    raise Exception("Failed to insert cashback history")
            
            return {
                'success': True if response.get('status') == 'success' else False,
                'data': {
                    **data_plan,
                    **history_response.data[0],
                    'data_bonus': format_data_amount(data_plan.get('cash_back') or return_cashback) if response.get('status') == 'success' else None,
                },
                'status': 'pending' if response.get('status') == 'pending' else None
            }
        
        
        if response.get('status') in ['fail', 'failed', 'error']:
            response_message = response.get('message')

            cw = charge_wallet(
                payment_method,
                amount=amount,
                refund=True
            )

            if cw and cw.get('error'):
                raise RuntimeError(cw.get('error'))

            payload['amount'] = amount
            if response_message and 'Insufficient' in response_message:
                payload['description'] = f'Data subscription of {data_plan.get("quantity")} failed for {phone}.'
            else:
                payload['description'] = response_message or f'Data subscription failed for {phone}.'
            payload['balance_after'] = balance
            payload['status'] = 'failed'

            history_response = supabase.table('history')\
                .insert(payload)\
                .execute()
            
            if not history_response.data:
                raise Exception("Failed to insert failed transaction history")
            
            return {
                'success': False,
                'data': {
                    **data_plan,
                    **history_response.data[0],
                }
            }
        
        else:
            raise Exception('An unknown occured while trying to process request.')
        

    if category == 'regular':
        plan_id = request.data.get('plan_id')

        if not plan_id:
            raise ValueError('Plan ID as plan_id is required.')
        
        data_plan = (supabase.table('vtpass')\
            .select('*')\
            .eq('id', plan_id).single().execute()).data
        
        amount = data_plan.get('price', 0) + data_plan.get('commission', 0)

        cw = charge_wallet(amount=amount, method=payment_method)

        if cw and cw.get('error'):
            raise Exception(cw.get('error'))

        response = get_regular_bundle(
            phone=phone,
            serviceID=data_plan.get('service_id'),
            request_id=generate(size=24),
            variation_code=data_plan.get('value'),
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
            'title': 'Data Subscription',
            'status': 'success',
            'description': f'Data bundle purchased successfully for {phone}',
            'user': request.user.id,
            'amount': amount,
            'provider': 'vtpass',
            'type': 'data_topup',
            'commission': commission,
            'balance_before': balance,
            'balance_after': (balance - amount) if payment_method == 'wallet' else None,
        }

        return_cashback = amount * CASHBACK_VALUE

        if code == '000':

            history_response = supabase.table('history')\
                .insert(payload)\
                .execute()
            
            if not history_response.data:
                raise Exception("Failed to insert transaction history")

            payload['title'] = 'Data Bonus'
            payload['description'] = f'You have successfully received a data bonus of {format_data_amount(return_cashback)}.'
            payload['amount'] = return_cashback
            payload['type'] = 'cashback'
            payload['transaction_id'] = content.get('transactions', {}).get('transactionId', '')
            payload['commission'] = commission + data_plan.get('commission', 0)
            payload['meta_data'] = {
                    **data_plan,
                    'data_bonus': format_data_amount(return_cashback),
                    'phone': phone,
                    'network': data_plan.get('network')
                }

            cashback_response = supabase.table('history')\
                .insert(payload)\
                .execute()
            
            if not cashback_response.data:
                raise Exception("Failed to insert cashback history")
            
            return {
                'success': True,
                'data': {
                    **data_plan,
                    **history_response.data[0],
                    'data_bonus': format_data_amount(return_cashback),
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
                'data': {
                    **data_plan,
                    **history_response.data[0]
                },
                'status': 'pending'
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
            payload['balance_after'] = balance if payment_method == 'wallet' else None

            history_response = supabase.table('history')\
                .insert(payload)\
                .execute()
            
            if not history_response.data:
                raise Exception("Failed to insert failed transaction history")
            
            return {
                'success': False,
                'data': {
                    **data_plan,
                    **history_response.data[0]
                }
            }

    else:
        raise Exception('The selected category could not be recognized.')