from rest_framework.views import APIView
from mobile.beneficiaries import save_beneficiary
from mobile.electricity import verify_merchant, process_electricity
from mobile.education import verify_education_merchant, process_education
from mobile.monnify import generate_reserved_account
from utils.response import ResponseMixin
from rest_framework import status
from utils import CASHBACK_VALUE, format_data_amount
import datetime
import logging

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from auth.supabase import SupabaseAuthentication
from .account import generate_palmpay_account

from supabase import Client

logger = logging.getLogger(__name__)


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
            
            try:
                palm_req = generate_palmpay_account(request)
                print("*" * 13, '\n')
                print(palm_req)
                print("*" * 13, '\n')
            except:
                pass

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

    def get(self, request, transaction_id=None):
        """
        GET /transactions/  —  return paginated transaction history
        GET /transactions/<id>/  —  return specific transaction details
        
        Query params (for list view):
            - limit: number of records to return (default: 30)
            - offset: number of records to skip (default: 0)
        """
        try:
            user = request.user
            if not user:
                return self.response(
                    error="Authentication required",
                    status_code=status.HTTP_401_UNAUTHORIZED
                )

            supabase = request.supabase_client

            if transaction_id:
                response = supabase.table('history')\
                    .select('*')\
                    .eq('id', int(transaction_id))\
                    .eq('user', user.id)\
                    .single()\
                    .execute()

                if not response.data:
                    return self.response(
                        error={"detail": "Transaction not found"},
                        status_code=status.HTTP_404_NOT_FOUND,
                        message="Transaction could not be found."
                    )

                return self.response(
                    data=response.data,
                    status_code=status.HTTP_200_OK,
                    message="Transaction retrieved successfully."
                )

            limit = int(request.query_params.get('limit', 30))
            offset = int(request.query_params.get('offset', 0))

            count_response = supabase.table('history').select('*', count='exact').eq('user', user.id).execute()
            total_count = count_response.count

            response = supabase.table('history')\
                .select('*')\
                .eq('user', user.id)\
                .order('created_at', desc=True)\
                .range(offset, offset + limit - 1)\
                .execute()

            return self.response(
                data=response.data,
                count=total_count,
                next=offset + limit if offset + limit < total_count else None,
                previous=offset - limit if offset > 0 else None,
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
    permission_classes = []

    def post(self, request):
        """
        POST /process-transactions/  —  process a new transaction
        """
        try:
            request.data['source'] = request.data.get('source', 'mobile')
        except:
            pass

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
                    
                    save_beneficiary(request)

                    if (not result.get('success')) and (result.get('data', {}).get('status') == 'pending'):
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
                    
                    save_beneficiary(request)
                    
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
                    return self.response(
                        error={"detail": str(e)},
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        message=str(e) if hasattr(e, '__str__') else "An unknown error occurred"
                    )
            
            
            if request.data.get('channel') == 'electricity':
                from .electricity import process_electricity

                try:
                    result = process_electricity(request)

                    if result.get('success'):
                        return self.response(
                            data=result.get('data'),
                            status_code=status.HTTP_200_OK,
                            message='Electricity bill paid successfully.'
                        )
                    
                    save_beneficiary(request)
                    
                    if (not result.get('success')) and (result.get('status') == 'pending'):
                        return self.response(
                            data=result.get('data'),
                            status_code=status.HTTP_200_OK,
                            message='Electricity payment is pending'
                        )
                    
                    else:
                        return self.response(
                            data=result.get('data'),
                            status_code=status.HTTP_400_BAD_REQUEST,
                            message='Electricity payment failed, please try again.'
                        )
                
                except Exception as e:
                    print(e)
                    return self.response(
                        error={"detail": str(e)},
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        message=str(e) if hasattr(e, '__str__') else "An unknown error occurred"
                    )

            if request.data.get('channel') == 'education':
                try:

                    result = process_education(request)

                    if result.get('success'):
                        return self.response(
                            data=result.get('data'),
                            status_code=status.HTTP_200_OK,
                            message="Education service purchased successfully"
                        )
                    else:
                        status_text = result.get('status', 'failed')
                        if status_text == 'pending':
                            return self.response(
                                data=result.get('data'),
                                status_code=status.HTTP_202_ACCEPTED,
                                message="Education service purchase is pending"
                            )
                        else:
                            return self.response(
                                data=result.get('data'),
                                error={"detail": "Transaction failed"},
                                status_code=status.HTTP_400_BAD_REQUEST,
                                message="Education service purchase failed"
                            )

                except ValueError as e:
                    return self.response(
                        error={"detail": str(e)},
                        status_code=status.HTTP_400_BAD_REQUEST,
                        message=str(e)
                    )
                except Exception as e:
                    print(e)
                    return self.response(
                        error={"detail": str(e)},
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        message="An unknown error occurred"
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
    permission_classes = []
    
    def post(self, request):
        from .bcrypt import verify_pin, hash_pin
        
        pin = request.data.get('pin')
        action = request.data.get('action', 'verify')

        if not pin:
            return self.response(
                error={"detail": "PIN is required"},
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Missing PIN"
            )
        
        try:
            if action in ['new', 'reset']:
                hashed_pin = hash_pin(pin)
                
                response = request.supabase_client.table('profile')\
                    .update({'pin': hashed_pin, 'onboarded': True})\
                    .eq('id', request.user.id)\
                    .execute()
                
                return self.response(
                    data={"pin_set": True},
                    status_code=status.HTTP_200_OK,
                    message="PIN set successfully"
                )
            
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
        GET /list-plans/  —  return 3 most recent transactions
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

            regular_plans = supabase.table('vtpass')\
                .select('*')\
                .eq('is_active', True)\
                .execute()
            
            regular_plans = [{
                **plan,
                'price': plan.get('price', 0) + plan.get('commission', 0), # This has to be done for DB commissioning
                'data_bonus': format_data_amount(plan.get('price', 0) * CASHBACK_VALUE)
            } for plan in regular_plans.data]
            
            payload = {
                'Super': super_plans,
                'Best': best_plans,
                'Regular': regular_plans
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
        

@method_decorator(csrf_exempt, name="dispatch")
class VerifyPhoneNumberView(APIView, ResponseMixin):
    permission_classes = []

    def post(self, request):
        """
        POST /verify-phone/  —  verify a phone number and return network carrier
        """
        try:
            phone: str | None = request.data.get('phone')
            if not phone:
                return self.response(
                    error={"detail": "Phone number is required"},
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message="Please provide a phone number"
                )

            from utils import verify_number
            network = verify_number(phone)

            if not network:
                return self.response(
                    error={"detail": "Could not verify phone number"},
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message="Unable to verify phone number. Please check and try again."
                )

            return self.response(
                data={"network": network},
                status_code=status.HTTP_200_OK,
                message="Phone number verified successfully"
            )

        except Exception as e:
            print(e)
            return self.response(
                error={"detail": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="An unknown error occurred"
            )


class BeneficiariesView(APIView, ResponseMixin):
    permission_classes = []

    def get(self, request):
        """
        GET /beneficiaries/  —  return saved beneficiaries for the current user
        
        Query params:
            - limit: number of records to return (default: 5)
        """
        from .beneficiaries import get_saved_beneficiaries

        try:
            user = request.user
            if not user:
                return self.response(
                    error="Authentication required",
                    status_code=status.HTTP_401_UNAUTHORIZED
                )

            limit = int(request.query_params.get('limit', 5))
            
            beneficiaries = get_saved_beneficiaries(request, limit=limit)

            if beneficiaries is None:
                return self.response(
                    error={"detail": "Failed to retrieve beneficiaries"},
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    message="An error occurred while retrieving beneficiaries"
                )

            return self.response(
                data=beneficiaries,
                status_code=status.HTTP_200_OK,
                message="Beneficiaries retrieved successfully"
            )

        except Exception as e:
            print(e)
            return self.response(
                error={"detail": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="An unknown error occurred"
            )


class ListElectricityView(APIView, ResponseMixin):
    permission_classes = []
    authentication_classes = []

    def get(self, request):
        """
        GET /list-electricity/
        """
        try:
            supabase: Client = request.supabase_client

            services = supabase.table('electricity')\
                .select('*')\
                .execute()
            
            return self.response(
                data=services.data,
                status_code=status.HTTP_200_OK,
            )

        except Exception as e:
            print(e)
            return self.response(
                error={"detail": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=str(e) if hasattr(e, '__str__') else "An unknown error occurred"
            )
        

class ListTVCableView(APIView, ResponseMixin):
    permission_classes = []
    authentication_classes = []

    def get(self, request):
        """
        GET /list-tv/
        """
        try:
            supabase: Client = request.supabase_client

            services = supabase.table('tv')\
                .select('*')\
                .execute()
            
            grouped_services = {}
            for service in services.data:
                provider = service.get('provider', '').lower()
                if provider not in grouped_services:
                    grouped_services[provider] = []
                grouped_services[provider].append(service)
            
            return self.response(
                data=grouped_services,
                status_code=status.HTTP_200_OK,
            )

        except Exception as e:
            print(e)
            return self.response(
                error={"detail": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=str(e) if hasattr(e, '__str__') else "An unknown error occurred"
            )
        

class AppConfig(APIView, ResponseMixin):
    permission_classes = []
    authentication_classes = []


    def get(self, request):

        import datetime

        """
        GET /app-config/
        """
        try:
            supabase: Client = request.supabase_client

            services = supabase.table('app_config')\
                .select('*')\
                .execute()
            
            config_map = {
                'jamb_price': {'default': 0.0, 'type': float},
                'waec_price': {'default': 0.0, 'type': float},
                'electricity_commission_rate': {'default': 0.1, 'type': float},
                'cashback_rate': {'default': CASHBACK_VALUE, 'type': float},
                'update_available': {'default': False, 'type': lambda x: x.lower() == 'true'},
                'update_url': {'default': '', 'type': str},
                'update_message': {'default': '', 'type': str},
            }

            config_values = {}
            for name, config in config_map.items():
                row = next((item for item in services.data if item.get('name') == name), None)
                if row:
                    value = row.get('value', config['default'])
                    if value is not None:
                        config_values[name] = config['type'](value)
                    else:
                        config_values[name] = config['default']
                else:
                    config_values[name] = config['default']

            current_date = datetime.datetime.now()
            year = current_date.year % 100
            month = current_date.month
            app_version = f"{year}.{month}"

            payload = {
                'app_name': 'isubscribe',
                'app_version': app_version,
                'support_email': 'support@isubscribe.com',
                'support_phone': '+2347049597498',
                **config_values,
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


@method_decorator(csrf_exempt, name="dispatch")
class VerifyMerchantView(APIView, ResponseMixin):
    permission_classes = []

    def post(self, request):
        """
        POST /verify-merchant/  —  verify merchant details for electricity services
        """
        try:
            user = request.user
            if not user:
                return self.response(
                    error="Authentication required",
                    status_code=status.HTTP_401_UNAUTHORIZED
                )

            type_param = request.data.get('type')
            service_id = request.data.get('serviceID')
            billers_code = request.data.get('billersCode')

            if not all([type_param, service_id, billers_code]):
                return self.response(
                    error={"detail": "Type, Service ID, and Billers code are required"},
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message="Please provide all required fields: type, service ID, and billers code"
                )


            result = verify_merchant(
                type=type_param,
                serviceID=service_id,
                billersCode=billers_code
            )

            if not result:
                return self.response(
                    error={"detail": "Failed to verify merchant"},
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message="Unable to verify merchant details. Please try again."
                )
            
            if result.get('code') != '000':
                return self.response(
                    error={"detail": result.get('message', 'Unknown error')},
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message="Merchant verification failed: " + result.get('message', 'Unknown error')
                )

            if result.get('content', {}).get('error'):
                return self.response(
                    error={"detail": result.get('content', {}).get('error')},
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message=f"Merchant verification failed: {result.get('content', {}).get('error')}"
                )

            return self.response(
                data=result.get('content', {}),
                status_code=status.HTTP_200_OK,
                message="Merchant verified successfully"
            )

        except Exception as e:
            print(e)
            return self.response(
                error={"detail": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="An unknown error occurred"
            )


@method_decorator(csrf_exempt, name="dispatch")
class VerifyEducationMerchantView(APIView, ResponseMixin):
    permission_classes = []

    def post(self, request):
        """
        POST /verify-education-merchant/  —  verify education merchant details (JAMB Profile ID)
        """
        try:
            user = request.user
            if not user:
                return self.response(
                    error="Authentication required",
                    status_code=status.HTTP_401_UNAUTHORIZED
                )

            service_id = request.data.get('serviceID')
            billers_code = request.data.get('billersCode') or request.data.get('profile_id')
            variation_code = request.data.get('variation_code')

            if not all([service_id, billers_code, variation_code]):
                return self.response(
                    error={"detail": "Service ID, Profile ID, and variation code are required"},
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message="Please provide all required fields: serviceID, profile_id (billersCode), and variation_code"
                )

            # Only JAMB and DE require verification
            if service_id not in ['jamb', 'de']:
                return self.response(
                    error={"detail": "Verification only required for JAMB and Direct Entry services"},
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message="This service does not require merchant verification"
                )

            result = verify_education_merchant(
                serviceID=service_id,
                billersCode=billers_code,
                variation_code=variation_code
            )

            if not result:
                return self.response(
                    error={"detail": "Failed to verify education merchant"},
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message="Unable to verify Profile ID. Please check and try again."
                )
            
            if result.get('code') != '000':
                return self.response(
                    error={"detail": result.get('message', 'Unknown error')},
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message="Profile ID verification failed: " + result.get('message', 'Unknown error')
                )

            return self.response(
                data=result.get('content', {}),
                status_code=status.HTTP_200_OK,
                message="Profile ID verified successfully"
            )

        except Exception as e:
            print(e)
            return self.response(
                error={"detail": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="An unknown error occurred"
            )


class ListEducationServicesView(APIView, ResponseMixin):
    permission_classes = []
    authentication_classes = []

    def get(self, request):
        """
        GET /list-education/  —  return available education services
        """
        try:
            supabase: Client = request.supabase_client

            services = supabase.table('education')\
                .select('*')\
                .eq('is_active', True)\
                .execute()
            
            # Group services by type
            grouped_services = {}
            for service in services.data:
                service_type = service.get('service_type', 'other')
                if service_type not in grouped_services:
                    grouped_services[service_type] = []
                
                # Calculate total price including commission
                base_price = float(service.get('price', 0))
                commission_rate = float(service.get('commission_rate', 0.1))
                total_price = base_price * (1 + commission_rate)
                
                service_info = {
                    **service,
                    'total_price': total_price,
                    'display_price': f"₦{total_price:.2f}"
                }
                grouped_services[service_type].append(service_info)
            
            return self.response(
                data=grouped_services,
                status_code=status.HTTP_200_OK,
            )

        except Exception as e:
            print(e)
            return self.response(
                error={"detail": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=str(e) if hasattr(e, '__str__') else "An unknown error occurred"
            )


@method_decorator(csrf_exempt, name="dispatch")
class RatingsView(APIView, ResponseMixin):
    permission_classes = []

    def post(self, request):
        """
        POST /ratings/  —  submit a user rating
        """
        try:
            user = request.user
            if not user:
                return self.response(
                    error="Authentication required",
                    status_code=status.HTTP_401_UNAUTHORIZED
                )

            rating = request.data.get('rating')
            comment = request.data.get('comment')

            if not rating:
                return self.response(
                    error={"detail": "Rating is required"},
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message="Please provide a rating"
                )

            if not isinstance(rating, (int, float)) or rating < 1 or rating > 5:
                return self.response(
                    error={"detail": "Rating must be between 1 and 5"},
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message="Rating must be a number between 1 and 5"
                )

            supabase = request.supabase_client

            data = {
                'user_id': user.id,
                'rating': rating,
                'comment': comment,
                'status': 'active'
            }

            response = supabase.table('ratings').insert(data).execute()

            if not response.data:
                return self.response(
                    error={"detail": "Failed to submit rating"},
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    message="Failed to submit rating"
                )

            return self.response(
                data=response.data[0],
                status_code=status.HTTP_201_CREATED,
                message="Rating submitted successfully"
            )

        except Exception as e:
            print(e)
            return self.response(
                error={"detail": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="An unknown error occurred"
            )

    def get(self, request):
        """
        GET /ratings/  —  get paginated active published ratings
        
        Query params:
            - limit: number of records to return (default: 20)
            - offset: number of records to skip (default: 0)
        """
        try:
            supabase = request.supabase_client

            limit = int(request.query_params.get('limit', 20))
            offset = int(request.query_params.get('offset', 0))

            response = supabase.table('ratings')\
                .select('*')\
                .eq('status', 'published')\
                .order('created_at', desc=True)\
                .range(offset, offset + limit - 1)\
                .execute()

            return self.response(
                data=response.data,
                status_code=status.HTTP_200_OK,
                message="Ratings retrieved successfully"
            )

        except Exception as e:
            print(e)
            return self.response(
                error={"detail": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="An unknown error occurred"
            )


@method_decorator(csrf_exempt, name="dispatch")
class DeleteAccountView(APIView, ResponseMixin):
    permission_classes = []

    def delete(self, request):
        """
        DELETE /delete-account/  —  delete the current user's account
        """
        try:
            user = request.user
            if not user:
                return self.response(
                    error="Authentication required",
                    status_code=status.HTTP_401_UNAUTHORIZED
                )

            supabase = request.supabase_client

            try:
                profile_response = supabase.table('profile')\
                    .select('id')\
                    .eq('id', user.id)\
                    .single()\
                    .execute()
                
                if not profile_response.data:
                    return self.response(
                        error={"detail": "Account not found or access denied"},
                        status_code=status.HTTP_403_FORBIDDEN,
                        message="You can only delete your own account"
                    )
            except Exception:
                return self.response(
                    error={"detail": "Account verification failed"},
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="Unable to verify account ownership"
                )

            tables_to_clean = ['wallet', 'history', 'beneficiaries', 'profile', 'ratings']
            
            for table in tables_to_clean:
                try:
                    supabase.table(table).delete().eq('user_id' if table == 'ratings' else 'user', user.id).execute()
                except:
                    pass

            try:
                from services.supabase import superbase
                superbase.auth.admin.delete_user(user.id)
            except Exception as e:
                print(f"Failed to delete user from auth: {e}")
                return self.response(
                    error={"detail": "Failed to delete account"},
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    message="Failed to delete account"
                )

            return self.response(
                data={"deleted": True},
                status_code=status.HTTP_200_OK,
                message="Account deleted successfully"
            )

        except Exception as e:
            print(e)
            return self.response(
                error={"detail": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="An unknown error occurred"
            )
        

@method_decorator(csrf_exempt, name="dispatch")
class GenerateReservedAccountView(APIView, ResponseMixin):
    permission_classes = []

    def post(self, request):
        """
        POST /reserved-account/  —  generate a reserved account for the current user
        
        Request body (optional):
            - bvn: User's Bank Verification Number
            - nin: User's National Identification Number
        """
        try:
            user = request.user
            if not user:
                return self.response(
                    error="Authentication required",
                    status_code=status.HTTP_401_UNAUTHORIZED
                )


            result = generate_reserved_account(request)

            if result.get('error'):
                return self.response(
                    error=result.get('error'),
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message=result.get('error', {}).get('message', 'Failed to generate reserved account')
                )

            return self.response(
                data=result.get('data'),
                status_code=status.HTTP_201_CREATED,
                message="Reserved account generated successfully"
            )

        except Exception as e:
            print(e)
            return self.response(
                error={"detail": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="An unknown error occurred while generating reserved account"
            )

    def get(self, request):
        """
        GET /reserved-account/  —  get existing reserved account for the current user
        """
        try:
            user = request.user
            if not user:
                return self.response(
                    error="Authentication required",
                    status_code=status.HTTP_401_UNAUTHORIZED
                )

            supabase = request.supabase_client

            response = supabase.table('accounts')\
                .select('*')\
                .eq('user', user.id)\
                .single()\
                .execute()

            if not response.data:
                return self.response(
                    error={"detail": "No reserved account found"},
                    status_code=status.HTTP_404_NOT_FOUND,
                    message="No reserved account found for this user"
                )

            return self.response(
                data=response.data,
                status_code=status.HTTP_200_OK,
                message="Reserved account retrieved successfully"
            )

        except Exception as e:
            print(e)
            return self.response(
                error={"detail": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="An unknown error occurred while retrieving reserved account"
            )



@method_decorator(csrf_exempt, name='dispatch')
class PushTokenView(APIView, ResponseMixin):
    """
    """
    permission_classes = []
    
    def get(self, request):
        """
        GET /mobile/push-tokens/
        
        Query params:
        - limit: Number of tokens to return (default: 50)
        - offset: Number of tokens to skip (default: 0)
        - user_id: Filter by specific user ID
        - active: Filter by active status (true/false)
        
        Returns paginated list of push tokens with user information
        """
        try:
            supabase: Client = request.supabase_client

            limit = int(request.query_params.get('limit', 50))
            offset = int(request.query_params.get('offset', 0))
            user_id = request.query_params.get('user_id')
            active = request.query_params.get('active')
            
            query = supabase.table('push_tokens').select(
                'id, token, user, active, created_at'
            )
            
            if user_id:
                query = query.eq('user', user_id)
            
            if active is not None:
                query = query.eq('active', active.lower() == 'true')
            
            count_response = query.execute()
            total_count = len(count_response.data) if count_response.data else 0
            
            tokens_response = query.order('created_at', desc=True).range(
                offset, offset + limit - 1
            ).execute()
            
            return self.response(
                data=tokens_response.data,
                count=total_count,
                next=offset + limit if offset + limit < total_count else None,
                previous=offset - limit if offset > 0 else None,
                message="Push tokens retrieved successfully",
                status_code=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.exception(f"Error in push token list: {str(e)}")
            return self.response(
                error={"detail": str(e)},
                message="Failed to retrieve push tokens",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request):
        """
        POST /mobile/push-tokens/
        
        Create or update push tokens for a user
        
        Request body:
        {
            "user_id": "uuid",
            "token": "push_token",
            "active": true|false,
            "device_type": "android|ios|web"  # Optional, for future use
        }
        """
        try:
            supabase: Client = request.supabase_client

            user_id = request.data.get('user_id')
            token = request.data.get('token')
            active = request.data.get('active', True)
            device_type = request.data.get('device_type', 'android')
            
            if not user_id or not token:
                return self.response(
                    error={"detail": "User ID and token are required"},
                    message="User ID and token are required",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            upsert_response = supabase.table('push_tokens').upsert({
                'user': user_id,
                'token': token,
                'active': active,
                'device_type': device_type
            }).execute()
            
            return self.response(
                data=upsert_response.data[0] if upsert_response.data else {},
                message="Push token created/updated successfully",
                status_code=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            logger.exception(f"Error in push token create/update: {str(e)}")
            return self.response(
                error={"detail": str(e)},
                message="Failed to create/update push token",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

@method_decorator(csrf_exempt, name='dispatch')
class ProfileView(APIView, ResponseMixin):
    """
    View for managing user profile information
    """
    permission_classes = []
    
    def get(self, request):
        """
        GET /mobile/profile/
        
        Returns the current user's profile information
        """
        try:
            user = request.user
            if not user:
                return self.response(
                    error="Authentication required",
                    status_code=status.HTTP_401_UNAUTHORIZED
                )
            
            supabase: Client = request.supabase_client
            
            profile_response = supabase.table('profile')\
                .select('*')\
                .eq('id', user.id)\
                .single()\
                .execute()
            
            if not profile_response.data:
                return self.response(
                    error={"detail": "Profile not found"},
                    status_code=status.HTTP_404_NOT_FOUND,
                    message="Profile not found"
                )
            
            return self.response(
                data=profile_response.data,
                status_code=status.HTTP_200_OK,
                message="Profile retrieved successfully"
            )
            
        except Exception as e:
            logger.exception(f"Error retrieving profile: {str(e)}")
            return self.response(
                error={"detail": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Failed to retrieve profile"
            )
        
    def put(self, request):
        """
        PUT /mobile/profile/

        Update the current user's profile information
        
        Request body:
        {
            "full_name": "New Name",
            "phone": "<New Phone Number>",
            "email": "<New Email Address>",
            "state": "<New State>",
            "username": "<New Username>"
        }
        """
        try:
            user = request.user
            if not user:
                return self.response(
                    error="Authentication required",
                    status_code=status.HTTP_401_UNAUTHORIZED
                )

            supabase: Client = request.supabase_client

            profile_data = {
                'full_name': request.data.get('full_name'),
                'phone': request.data.get('phone'),
                'email': request.data.get('email'),
                'state': request.data.get('state'),
                'username': request.data.get('username'),
                'updated_at': datetime.datetime.now().isoformat()
            }

            if profile_data.get('email'):
                try:
                    from services.supabase import superbase
                    superbase.auth.admin.update_user_by_id(
                        uid=user.id,
                        attributes={"email": profile_data['email']},
                    )
                except Exception as e:
                    logger.exception(f"Failed to update user email: {str(e)}")
                    return self.response(
                        error={"detail": str(e)},
                        status_code=status.HTTP_400_BAD_REQUEST,
                        message="Failed to update email address"
                    )
                
            update_response = supabase.table('profile').update(profile_data).eq('id', user.id).execute()

            if not update_response.data:
                return self.response(
                    error={"detail": "Profile update failed"},
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message="Profile update failed"
                )

            return self.response(
                data=update_response.data,
                status_code=status.HTTP_200_OK,
                message="Profile updated successfully"
            )

        except Exception as e:
            logger.exception(f"Error updating profile: {str(e)}")
            return self.response(
                error={"detail": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Failed to update profile"
            )