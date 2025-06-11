from rest_framework.views import APIView
from utils.response import ResponseMixin
from rest_framework import status
from utils import format_data_amount

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from auth.supabase import SupabaseAuthentication

from supabase import Client


class WalletAPIView(APIView, ResponseMixin):
    permission_classes = []

    def get(self, request):
        """
        GET /wallets/  —  return the current user's wallet balance
        """
        try:
            user = request.user
            if not user:
                return self.response(
                    error="Authentication required",
                    status_code=status.HTTP_401_UNAUTHORIZED
                )

            supabase = request.supabase_client

            response = supabase.table('wallet').select('*').eq('user', user.id).single().execute()

            payload = {
                'balance': response.data.get('balance'),
                'cashback_balance': response.data.get('cashback_balance'),
                'data_bonus': format_data_amount(response.data.get('cashback_balance')),
            }
            
            if not response.data:
                return self.response(
                    error={"detail": "Wallet not found"},
                    message="Wallet not found",
                    status_code=status.HTTP_404_NOT_FOUND
                )

            wallet = response.data
            return self.response(
                data=payload,
                status_code=status.HTTP_200_OK,
            )

        except Exception as e:
            print(e)
            return self.response(
                error={"detail": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="An unknown error occurred"
            )


class TransactionHistoryView(APIView, ResponseMixin):
    
    permission_classes = []

    def get(self, request):
        """
        GET /transactions/  —  return paginated transaction history
        Query params:
            - limit: number of records to return (default: 10)
            - offset: number of records to skip (default: 0)
        """
        try:
            user = request.user
            if not user:
                return self.response(
                    error="Authentication required",
                    status_code=status.HTTP_401_UNAUTHORIZED
                )

            limit = int(request.query_params.get('limit', 30))
            offset = int(request.query_params.get('offset', 0))

            supabase = request.supabase_client

            count_response = supabase.table('history').select('*', count='exact').eq('user', user.id).execute()
            total_count = count_response.count

            response = supabase.table('history')\
                .select('*')\
                .eq('user', user.id)\
                .order('created_at', desc=True)\
                .range(offset, offset + limit - 1)\
                .execute()

            return self.response(
                data={
                    'transactions': response.data,
                    'total': total_count,
                    'limit': limit,
                    'offset': offset
                },
                status_code=status.HTTP_200_OK,
            )

        except Exception as e:
            print(e)
            return self.response(
                error={"detail": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="An unknown error occurred"
            )


class LatestTransactionsView(APIView, ResponseMixin):
    permission_classes = []

    def get(self, request):
        """
        GET /transactions/latest/  —  return 3 most recent transactions
        """
        try:
            user = request.user
            if not user:
                return self.response(
                    error="Authentication required",
                    status_code=status.HTTP_401_UNAUTHORIZED
                )

            supabase = request.supabase_client

            response = supabase.table('history')\
                .select('*')\
                .eq('user', user.id)\
                .order('created_at', desc=True)\
                .limit(3)\
                .execute()
            
            return self.response(
                data=response.data,
                status_code=status.HTTP_200_OK,
            )

        except Exception as e:
            print(e)
            return self.response(
                error={"detail": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="An unknown error occurred"
            )
        

@method_decorator(csrf_exempt, name="dispatch")
class ProcessTransaction(APIView, ResponseMixin):
    authentication_classes = [SupabaseAuthentication]
    permission_classes = []

    def post(self, request):
        """
        POST /process-transactions/  —  process a new transaction
        """
        try:
            user = request.user
            if not user:
                return self.response(
                    error="Authentication required",
                    status_code=status.HTTP_401_UNAUTHORIZED
                )

            if request.data.get('channel') == 'airtime':
                from .airtime import process_airtime

                try:
                    result = process_airtime(request)

                    if result.get('success'):
                        return self.response(
                            data=result.get('data'),
                            status_code=status.HTTP_200_OK,
                            message='Airtime purchased successfully.'
                        )
                    
                    if (not result.get('success')) and (result.get('data').get('status') == 'pending'):
                        return self.response(
                            data=result.get('data'),
                            status_code=status.HTTP_200_OK,
                            message='Airtime purchase is pending'
                        )
                    
                    else:
                        return self.response(
                            data=result.get('data'),
                            status_code=status.HTTP_400_BAD_REQUEST,
                            message='Airtime purchase failed, please try again.'
                        )
                        
                except Exception as e:
                    print(e)
                    return self.response(
                        error={"detail": str(e)},
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        message=str(e) if hasattr(e, '__str__') else "An unknown error occurred"
                    )


            if request.data.get('channel') == 'data_bundle':
                from .data_bundle import process_data_bundle

                try:
                    result = process_data_bundle(request)

                    if result.get('success'):
                        return self.response(
                            data=result.get('data'),
                            status_code=status.HTTP_200_OK,
                            message='Data purchased successfully.'
                        )
                    
                    if (not result.get('success')) and (result.get('status') == 'pending'):
                        return self.response(
                            data=result.get('data'),
                            status_code=status.HTTP_200_OK,
                            message='Data purchase is pending'
                        )
                    
                    else:
                        return self.response(
                            data=result.get('data'),
                            status_code=status.HTTP_400_BAD_REQUEST,
                            message='Data purchase failed, please try again.'
                        )
                
                except Exception as e:
                    print(e)
                    self.response(
                        error={"detail": str(e)},
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        message=str(e) if hasattr(e, '__str__') else "An unknown error occurred"
                    )
            return self.response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="An unhandled server error occured.",
                error={'message': 'An unhandled server error has occured.'}
            )

        except Exception as e:
            print(e)
            return self.response(
                error={"detail": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=str(e) if hasattr(e, '__str__') else "An unknown error occurred"
            )


@method_decorator(csrf_exempt, name="dispatch")
class VerifyPinView(APIView, ResponseMixin):
    authentication_classes = [SupabaseAuthentication]
    permission_classes = []
    
    def post(self, request):
        from .bcrypt import verify_pin
        
        pin = request.data.get('pin')
        if not pin:
            return self.response(
                error={"detail": "PIN is required"},
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Missing PIN"
            )
        
        try:
            profile = request.supabase_client.table('profile')\
                .select('pin')\
                .eq('id', request.user.id)\
                .single()\
                .execute()
                
            if not profile.data:
                return self.response(
                    error={"detail": "Profile not found"},
                    status_code=status.HTTP_404_NOT_FOUND,
                    message="Profile not found"
                )
                
            hashed_pin = profile.data.get('pin')
            if not hashed_pin:
                return self.response(
                    error={"detail": "PIN not set"},
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message="PIN not set in profile"
                )
            
            is_valid = verify_pin(pin, hashed_pin)
            
            return self.response(
                data={"is_valid": is_valid},
                status_code=status.HTTP_200_OK,
                message="PIN verification completed"
            )
            
        except Exception as e:
            print(e)
            return self.response(
                error={"detail": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Failed to verify PIN"
            )


class ListDataPlansView(APIView, ResponseMixin):
    permission_classes = []
    authentication_classes = []

    def get(self, request):
        """
        GET /transactions/latest/  —  return 3 most recent transactions
        """
        try:
            from utils import CASHBACK_VALUE

            supabase: Client = request.supabase_client

            super_plans = supabase.table('n3t')\
                .select('*')\
                .eq('is_active', True)\
                .execute()
            
            super_plans = [{
                **plan,
                'data_bonus': format_data_amount(plan.get('price', 0) * CASHBACK_VALUE)
            } for plan in super_plans.data]
            
            best_plans = supabase.table('gsub')\
                .select('*')\
                .eq('is_active', True)\
                .execute()
            
            best_plans = [{
                **plan,
                'price': plan.get('price', 0) + plan.get('commission', 0), # This has to be done for DB commissioning
                'data_bonus': format_data_amount(plan.get('price', 0) * CASHBACK_VALUE)
            } for plan in best_plans.data]
            
            payload = {
                'Super': super_plans,
                'Best': best_plans,
                'Regular': []
            }
            
            return self.response(
                data=payload,
                status_code=status.HTTP_200_OK,
            )

        except Exception as e:
            print(e)
            return self.response(
                error={"detail": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=str(e) if hasattr(e, '__str__') else "An unknown error occurred"
            )
        