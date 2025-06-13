import requests
from typing import Any, Optional, TypedDict
from supabase import Client

def generate_palmpay_account(request: Any):
    """
    Generate a Palmpay virtual account for the user
    """
    try:
        from services.supabase import superbase as supabase
        
        user = request.user

        if not user:
            return {
                'data': None,
                'error': {'message': 'User not found'}
            }

        account = None

        try:
            account_response = supabase.table('account')\
            .select('*')\
            .eq('user', user.id)\
            .single()\
            .execute()

            account = account_response.data

            if account and account.get('palmpay_account_number'):
                return {
                    'data': None,
                    'error': {'message': 'Palmpay account already exists, please refresh.'}
                }
        except Exception as e:
            print("The Exception that occured while trying to generate a palmpay account is: ", e)


        try:
            response = requests.post(
                'https://isubscribe-ai-microservice.onrender.com/api/v1/palmpay/create_virtual_account/',
                json={
                    'email': user.email or '',
                    'customer_name': user.metadata.get('full_name') or '',
                }
            )


            if response.status_code == 201:
                req_data = response.json()

                print("Response from Palmpay: ", req_data)

                account_data = {
                    'palmpay_account_number': req_data['data']['virtual_account_no'],
                    'palmpay_account_name': req_data['data']['virtual_account_name'],
                    'metadata': {
                        'palmpay': req_data['data']
                    },
                    'user': user.id,
                }

                if account:
                    account_response = supabase.table('account')\
                        .update(account_data)\
                        .eq('id', account['id'])\
                        .execute()
                else:
                    account_response = supabase.table('account')\
                        .insert(account_data)\
                        .execute()

                return {
                    'data': account_response.data,
                    'error': None
                }

            else:
                return {
                    'data': None,
                    'error': {'message': f'Palmpay account creation failed with status: {response.status_code}'}
                }

        except Exception as e:
            print('//////', e)
            error_message = str(e)
            if hasattr(e, 'response') and e.response is not None:
                error_message = e.response.get('data', {}).get('message', str(e))
            
            return {
                'data': None,
                'error': {'message': error_message or 'Failed to create Palmpay account'}
            }

    except Exception as e:
        print('??????????', e)
        return {
            'data': None,
            'error': {'message': str(e)}
        }
