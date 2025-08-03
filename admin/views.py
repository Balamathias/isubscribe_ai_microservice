"""
iSubscribe Admin API Views

This module provides comprehensive admin API endpoints for the iSubscribe platform.
All endpoints follow the ResponseMixin pattern and provide detailed analytics,
monitoring, and management capabilities.

Endpoints:
- GET /admin/dashboard/ - Overall dashboard metrics
- GET /admin/analytics/users/ - User analytics and insights
- GET /admin/analytics/financial/ - Financial analytics and revenue
- GET /admin/analytics/transactions/ - Transaction monitoring and analysis
- GET /admin/analytics/services/ - Service performance analytics
- GET /admin/system/health/ - System health monitoring
- GET /admin/users/ - User management and search
- POST /admin/users/{id}/actions/ - User management actions
- GET /admin/transactions/ - Advanced transaction search and filtering
- GET /admin/reports/revenue/ - Revenue reports
- GET /admin/reports/export/ - Data export functionality
"""

from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
import csv
import io

from mobile.notifications import send_push_notification, send_bulk_push_notifications
from utils.response import ResponseMixin
from .services import (
    UserAnalyticsService,
    FinancialAnalyticsService,
    TransactionAnalyticsService,
    ServiceAnalyticsService,
    SystemHealthService
)
from .permissions import (
    IsAdminUser,
    IsSuperAdminUser,
    CanViewAnalytics,
    CanModifyUsers,
    CanViewFinancials,
    AdminSupabaseAuthentication
)
from services.supabase import superbase as supabase

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class AdminDashboardViewSet(ViewSet, ResponseMixin):
    """
    Main admin dashboard providing overview metrics and quick insights
    """
    authentication_classes = [AdminSupabaseAuthentication]
    permission_classes = [CanViewAnalytics]
    
    def list(self, request):
        """
        GET /admin/dashboard/
        
        Returns comprehensive dashboard overview including:
        - User metrics (total, new, active)
        - Financial overview (revenue, transactions)
        - System health status
        - Recent activities
        """
        try:
            days = int(request.query_params.get('days', 30))
            
            # Get overview metrics
            user_metrics = UserAnalyticsService.get_user_overview(days)
            financial_metrics = FinancialAnalyticsService.get_revenue_overview(days=days)
            transaction_metrics = TransactionAnalyticsService.get_transaction_overview(days)
            system_health = SystemHealthService.get_system_health()
            
            # Recent activities (latest transactions)
            recent_activities = supabase.table('history').select(
                'id, user, email, type, amount, status, created_at, description', 'profile (username, email, full_name)'
            ).order('created_at', desc=True).limit(10).execute()
            
            dashboard_data = {
                "overview": {
                    "total_users": user_metrics.get("total_users", 0),
                    "total_revenue": financial_metrics.get("total_revenue", 0),
                    "total_transactions": transaction_metrics.get("total_transactions", 0),
                    "success_rate": transaction_metrics.get("success_rate", 0),
                    "system_status": system_health.get("overall_status", "unknown")
                },
                "user_metrics": user_metrics,
                "financial_metrics": {
                    "total_revenue": financial_metrics.get("total_revenue", 0),
                    "total_volume": financial_metrics.get("total_volume", 0),
                    "success_rate": financial_metrics.get("success_rate", 0),
                    "daily_trends": financial_metrics.get("daily_trends", [])[:7]  # Last 7 days
                },
                "transaction_metrics": {
                    "total_transactions": transaction_metrics.get("total_transactions", 0),
                    "successful_transactions": transaction_metrics.get("successful_transactions", 0),
                    "failed_transactions": transaction_metrics.get("failed_transactions", 0),
                    "success_rate": transaction_metrics.get("success_rate", 0),
                    "transaction_types": transaction_metrics.get("transaction_types", {})
                },
                "system_health": system_health,
                "recent_activities": recent_activities.data if recent_activities.data else [],
                "period_days": days,
                "generated_at": datetime.now().isoformat()
            }
            
            return self.response(
                data=dashboard_data,
                message="Dashboard data retrieved successfully",
                status_code=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.exception(f"Error in admin dashboard: {str(e)}")
            return self.response(
                error={"detail": str(e)},
                message="Failed to retrieve dashboard data",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class AdminAnalyticsViewSet(ViewSet, ResponseMixin):
    """
    Comprehensive analytics endpoints for different aspects of the platform
    """
    authentication_classes = [AdminSupabaseAuthentication]
    permission_classes = [CanViewAnalytics]
    
    @action(detail=False, methods=['get'])
    def users(self, request):
        """
        GET /admin/analytics/users/
        
        Query params:
        - days: Number of days to analyze (default: 30)
        
        Returns detailed user analytics including growth, engagement, and demographics
        """
        try:
            days = int(request.query_params.get('days', 30))
            
            user_overview = UserAnalyticsService.get_user_overview(days)
            engagement_metrics = UserAnalyticsService.get_user_engagement_metrics(days)
            
            analytics_data = {
                **user_overview,
                "engagement_metrics": engagement_metrics,
                "generated_at": datetime.now().isoformat()
            }
            
            return self.response(
                data=analytics_data,
                message="User analytics retrieved successfully",
                status_code=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.exception(f"Error in user analytics: {str(e)}")
            return self.response(
                error={"detail": str(e)},
                message="Failed to retrieve user analytics",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def financial(self, request):
        """
        GET /admin/analytics/financial/
        
        Query params:
        - start_date: Start date (ISO format)
        - end_date: End date (ISO format)
        - days: Number of days if dates not provided (default: 30)
        
        Returns comprehensive financial analytics and revenue insights
        """
        try:
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            days = int(request.query_params.get('days', 30))
            
            financial_data = FinancialAnalyticsService.get_revenue_overview(
                start_date=start_date,
                end_date=end_date,
                days=days
            )
            
            return self.response(
                data=financial_data,
                message="Financial analytics retrieved successfully",
                status_code=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.exception(f"Error in financial analytics: {str(e)}")
            return self.response(
                error={"detail": str(e)},
                message="Failed to retrieve financial analytics",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def transactions(self, request):
        """
        GET /admin/analytics/transactions/
        
        Query params:
        - days: Number of days to analyze (default: 30)
        
        Returns transaction monitoring and analysis including suspicious activities
        """
        try:
            days = int(request.query_params.get('days', 30))
            
            transaction_data = TransactionAnalyticsService.get_transaction_overview(days)
            
            return self.response(
                data=transaction_data,
                message="Transaction analytics retrieved successfully",
                status_code=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.exception(f"Error in transaction analytics: {str(e)}")
            return self.response(
                error={"detail": str(e)},
                message="Failed to retrieve transaction analytics",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def services(self, request):
        """
        GET /admin/analytics/services/
        
        Query params:
        - days: Number of days to analyze (default: 30)
        
        Returns performance analytics for all services (data, airtime, bills, education)
        """
        try:
            days = int(request.query_params.get('days', 30))
            
            service_data = ServiceAnalyticsService.get_service_performance(days)
            
            return self.response(
                data=service_data,
                message="Service analytics retrieved successfully",
                status_code=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.exception(f"Error in service analytics: {str(e)}")
            return self.response(
                error={"detail": str(e)},
                message="Failed to retrieve service analytics",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class AdminSystemViewSet(ViewSet, ResponseMixin):
    """
    System monitoring and health check endpoints
    """
    authentication_classes = [AdminSupabaseAuthentication]
    permission_classes = [CanViewAnalytics]
    
    @action(detail=False, methods=['get'])
    def health(self, request):
        """
        GET /admin/system/health/
        
        Returns comprehensive system health metrics including:
        - Database connectivity and performance
        - Service availability
        - Error rates
        - Overall system status
        """
        try:
            health_data = SystemHealthService.get_system_health()
            
            return self.response(
                data=health_data,
                message="System health retrieved successfully",
                status_code=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.exception(f"Error in system health: {str(e)}")
            return self.response(
                error={"detail": str(e)},
                message="Failed to retrieve system health",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class AdminUserManagementViewSet(ViewSet, ResponseMixin):
    """
    User management endpoints for admin operations
    """
    authentication_classes = [AdminSupabaseAuthentication]
    permission_classes = [CanViewAnalytics]
    
    def list(self, request):
        """
        GET /admin/users/
        
        Query params:
        - limit: Number of users to return (default: 50)
        - offset: Number of users to skip (default: 0)
        - search: Search term for email, name, or phone
        - role: Filter by user role
        - status: Filter by user status
        - created_after: Filter users created after date
        - created_before: Filter users created before date
        
        Returns paginated list of users with detailed information
        """
        try:
            limit = int(request.query_params.get('limit', 50))
            offset = int(request.query_params.get('offset', 0))
            search = request.query_params.get('search', '').strip()
            role = request.query_params.get('role')
            created_after = request.query_params.get('created_after')
            created_before = request.query_params.get('created_before')
            
            # Build query
            query = supabase.table('profile').select(
                'id, email, full_name, phone, role, created_at, onboarded, state'
            )
            
            # Apply filters
            if search:
                # Simple search across multiple fields
                search_query = f"email.ilike.%{search}%,full_name.ilike.%{search}%,phone.ilike.%{search}%"
                query = query.or_(search_query)
            
            if role:
                query = query.eq('role', role)
            
            if created_after:
                query = query.gte('created_at', created_after)
            
            if created_before:
                query = query.lte('created_at', created_before)
            
            # Get total count
            count_response = query.execute()
            total_count = len(count_response.data) if count_response.data else 0
            
            # Get paginated results
            users_response = query.order('created_at', desc=True).range(
                offset, offset + limit - 1
            ).execute()
            
            # Enhance user data with wallet information
            enhanced_users = []
            if users_response.data:
                for user in users_response.data:
                    # Get user's wallet info
                    wallet_response = supabase.table('wallet').select(
                        'balance, cashback_balance'
                    ).eq('user', user['id']).execute()
                    
                    # Get user's transaction count
                    tx_count_response = supabase.table('history').select(
                        '*', count='exact'
                    ).eq('user', user['id']).execute()
                    
                    wallet_data = wallet_response.data[0] if wallet_response.data else {}
                    
                    enhanced_user = {
                        **user,
                        "wallet_balance": wallet_data.get('balance', 0),
                        "cashback_balance": wallet_data.get('cashback_balance', 0),
                        "transaction_count": tx_count_response.count or 0
                    }
                    enhanced_users.append(enhanced_user)
            
            return self.response(
                data=enhanced_users,
                count=total_count,
                next=offset + limit if offset + limit < total_count else None,
                previous=offset - limit if offset > 0 else None,
                message="Users retrieved successfully",
                status_code=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.exception(f"Error in user list: {str(e)}")
            return self.response(
                error={"detail": str(e)},
                message="Failed to retrieve users",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def retrieve(self, request, pk=None):
        """
        GET /admin/users/{id}/
        
        Returns detailed information about a specific user including:
        - Profile information
        - Wallet details
        - Transaction history summary
        - Account status and security info
        """
        try:
            if not pk:
                return self.response(
                    error={"detail": "User ID is required"},
                    message="User ID is required",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Get user profile
            user_response = supabase.table('profile').select('*').eq('id', pk).single().execute()
            
            if not user_response.data:
                return self.response(
                    error={"detail": "User not found"},
                    message="User not found",
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            user_data = user_response.data
            
            # Get wallet information
            wallet_response = supabase.table('wallet').select('*').eq('user', pk).single().execute()
            
            # Get transaction summary
            tx_summary_response = supabase.table('history').select(
                'status, type, amount, commission'
            ).eq('user', pk).execute()
            
            # Calculate transaction statistics
            tx_stats = {"total": 0, "success": 0, "failed": 0, "total_volume": 0, "total_commission": 0}
            if tx_summary_response.data:
                tx_stats["total"] = len(tx_summary_response.data)
                tx_stats["success"] = len([tx for tx in tx_summary_response.data if tx.get('status') == 'success'])
                tx_stats["failed"] = len([tx for tx in tx_summary_response.data if tx.get('status') == 'failed'])
                tx_stats["total_volume"] = sum(float(tx.get('amount', 0)) for tx in tx_summary_response.data if tx.get('amount'))
                tx_stats["total_commission"] = sum(float(tx.get('commission', 0)) for tx in tx_summary_response.data if tx.get('commission'))
            
            # Get account information
            account_response = supabase.table('account').select('*').eq('user', pk).single().execute()
            
            # Get referral information
            referral_response = supabase.table('referrals').select('*').eq('referred', pk).execute()
            
            user_detail = {
                "profile": user_data,
                "wallet": wallet_response.data if wallet_response.data else {},
                "transaction_summary": tx_stats,
                "account_info": account_response.data if account_response.data else {},
                "referral_info": referral_response.data if referral_response.data else [],
                "generated_at": datetime.now().isoformat()
            }
            
            return self.response(
                data=user_detail,
                message="User details retrieved successfully",
                status_code=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.exception(f"Error in user detail: {str(e)}")
            return self.response(
                error={"detail": str(e)},
                message="Failed to retrieve user details",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def actions(self, request, pk=None):
        """
        POST /admin/users/{id}/actions/
        
        Perform administrative actions on user accounts:
        - suspend: Suspend user account
        - activate: Activate user account
        - adjust_balance: Adjust wallet balance
        - reset_pin: Reset user PIN
        - set_role: Change user role
        
        Request body:
        {
            "action": "suspend|activate|adjust_balance|reset_pin|set_role",
            "amount": 100.0,  // For adjust_balance
            "role": "admin",  // For set_role
            "reason": "Admin action reason"
        }
        """
        try:
            if not pk:
                return self.response(
                    error={"detail": "User ID is required"},
                    message="User ID is required",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            action = request.data.get('action')
            reason = request.data.get('reason', 'Admin action')
            pin = request.data.get('pin')
            
            if not action:
                return self.response(
                    error={"detail": "Action is required"},
                    message="Action is required",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Verify user exists
            user_response = supabase.table('profile').select('id, email, full_name').eq('id', pk).single().execute()
            if not user_response.data:
                return self.response(
                    error={"detail": "User not found"},
                    message="User not found",
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            result = {}

            saved_pin: str | None = (supabase.table('profile').select('pin').eq('id', request.user.id).single().execute()).data.get('pin')

            from mobile.bcrypt import verify_pin

            is_pin_valid = verify_pin(pin, saved_pin) if (pin and saved_pin) else False

            if not is_pin_valid:
                return self.response(
                    error={"detail": "Invalid PIN"},
                    message="Invalid PIN",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            if action == 'suspend':
                # Update user role to suspended (you might want to add a status field)
                update_response = supabase.table('profile').update({
                    'role': 'suspended',
                    'updated_at': datetime.now().isoformat()
                }).eq('id', pk).execute()
                result = {"message": "User suspended successfully"}
                
            elif action == 'activate':
                # Reactivate user (set role back to user)
                update_response = supabase.table('profile').update({
                    'role': 'user',
                    'updated_at': datetime.now().isoformat()
                }).eq('id', pk).execute()
                result = {"message": "User activated successfully"}
                
            elif action == 'adjust_balance':
                amount = request.data.get('amount')
                if amount is None:
                    return self.response(
                        error={"detail": "Amount is required for balance adjustment"},
                        message="Amount is required",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
                
                # Use Supabase function to adjust balance
                adjust_response = supabase.rpc('modify_wallet_balance', {
                    'user_id': pk,
                    'amount': float(amount),
                }).execute()
                
                result = {"message": f"Balance adjusted by {amount}", "new_balance": amount}
                
            elif action == 'set_role':
                new_role = request.data.get('role')
                if not new_role:
                    return self.response(
                        error={"detail": "Role is required"},
                        message="Role is required",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
                
                update_response = supabase.table('profile').update({
                    'role': new_role,
                    'updated_at': datetime.now().isoformat()
                }).eq('id', pk).execute()
                result = {"message": f"User role updated to {new_role}"}
                
            elif action == 'reset_pin':
                # Clear the user's PIN (they'll need to set a new one)
                update_response = supabase.table('profile').update({
                    'pin': None,
                    'updated_at': datetime.now().isoformat()
                }).eq('id', pk).execute()
                result = {"message": "User PIN reset successfully"}
                
            else:
                return self.response(
                    error={"detail": "Invalid action"},
                    message="Invalid action",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Log the admin action
            admin_user = request.user
            logger.info(f"Admin action: {admin_user.email} performed '{action}' on user {pk}. Reason: {reason}")
            
            return self.response(
                data=result,
                message=result.get("message", "Action completed successfully"),
                status_code=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.exception(f"Error in user action: {str(e)}")
            return self.response(
                error={"detail": str(e)},
                message="Failed to perform user action",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class AdminTransactionViewSet(ViewSet, ResponseMixin):
    """
    Advanced transaction search and management endpoints
    """
    authentication_classes = [AdminSupabaseAuthentication]
    permission_classes = [CanViewFinancials]
    # authentication_classes = []
    # permission_classes = []
    
    def list(self, request):
        """
        GET /admin/transactions/
        
        Advanced transaction search with filters:
        - limit, offset: Pagination
        - search: Search in description, email, transaction_id
        - status: Filter by transaction status
        - type: Filter by transaction type
        - provider: Filter by provider
        - amount_min, amount_max: Amount range filter
        - date_from, date_to: Date range filter
        - user_id: Filter by specific user
        
        Returns detailed transaction list with user information
        """
        try:
            limit = int(request.query_params.get('limit', 50))
            offset = int(request.query_params.get('offset', 0))
            search = request.query_params.get('search', '').strip()
            status_filter = request.query_params.get('status')
            type_filter = request.query_params.get('type')
            provider_filter = request.query_params.get('provider')
            amount_min = request.query_params.get('amount_min')
            amount_max = request.query_params.get('amount_max')
            date_from = request.query_params.get('date_from')
            date_to = request.query_params.get('date_to')
            user_id = request.query_params.get('user_id')
            
            # Build query
            query = supabase.table('history').select('*, profile (email, full_name)')
            
            # Apply filters
            if search:
                search_terms = f"description.ilike.%{search}%,email.ilike.%{search}%,transaction_id.ilike.%{search}%"
                query = query.or_(search_terms)
            
            if status_filter:
                query = query.eq('status', status_filter)
            
            if type_filter:
                query = query.eq('type', type_filter)
            
            if provider_filter:
                query = query.eq('provider', provider_filter)
            
            if amount_min:
                query = query.gte('amount', float(amount_min))
            
            if amount_max:
                query = query.lte('amount', float(amount_max))
            
            if date_from:
                query = query.gte('created_at', date_from)
            
            if date_to:
                query = query.lte('created_at', date_to)
            
            if user_id:
                query = query.eq('user', user_id)
            
            # Get total count
            count_response = query.execute()
            total_count = len(count_response.data) if count_response.data else 0
            
            # Get paginated results
            transactions_response = query.order('created_at', desc=True).range(
                offset, offset + limit - 1
            ).execute()
            
            processed_transactions = []
            if transactions_response.data:
                for transaction in transactions_response.data:
                    if 'meta_data' in transaction and transaction['meta_data']:
                        import json

                        if isinstance(transaction['meta_data'], str):
                            try:
                                transaction['meta_data'] = json.loads(transaction['meta_data'])
                            except (json.JSONDecodeError, ValueError):
                                transaction['meta_data'] = {}
                        elif not isinstance(transaction['meta_data'], dict):
                            transaction['meta_data'] = {}
                    else:
                        transaction['meta_data'] = {}
                    
                    processed_transactions.append(transaction)
            
            return self.response(
                data=processed_transactions,
                count=total_count,
                next=offset + limit if offset + limit < total_count else None,
                previous=offset - limit if offset > 0 else None,
                message="Transactions retrieved successfully",
                status_code=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.exception(f"Error in transaction list: {str(e)}")
            return self.response(
                error={"detail": str(e)},
                message="Failed to retrieve transactions",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class AdminReportsViewSet(ViewSet, ResponseMixin):
    """
    Report generation and data export endpoints
    """
    authentication_classes = [AdminSupabaseAuthentication]
    permission_classes = [CanViewFinancials]
    
    @action(detail=False, methods=['get'])
    def revenue(self, request):
        """
        GET /admin/reports/revenue/
        
        Generate comprehensive revenue reports with:
        - Daily, weekly, monthly breakdowns
        - Service-wise revenue
        - Provider performance
        - Growth comparisons
        
        Query params:
        - period: daily, weekly, monthly (default: daily)
        - start_date, end_date: Date range
        - format: json, csv (default: json)
        """
        try:
            period = request.query_params.get('period', 'daily')
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            format_type = request.query_params.get('format', 'json')
            
            if not start_date or not end_date:
                # Default to last 30 days
                end_dt = datetime.now()
                start_dt = end_dt - timedelta(days=30)
                start_date = start_dt.isoformat()
                end_date = end_dt.isoformat()
            
            revenue_data = FinancialAnalyticsService.get_revenue_overview(start_date, end_date)
            
            if format_type == 'csv':
                # Generate CSV response
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = f'attachment; filename="revenue_report_{period}_{start_date}_{end_date}.csv"'
                
                writer = csv.writer(response)
                writer.writerow(['Date', 'Revenue', 'Volume', 'Transactions'])
                
                for trend in revenue_data.get('daily_trends', []):
                    writer.writerow([
                        trend['date'],
                        trend['revenue'],
                        trend['volume'],
                        trend['transactions']
                    ])
                
                return response
            
            return self.response(
                data=revenue_data,
                message="Revenue report generated successfully",
                status_code=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.exception(f"Error in revenue report: {str(e)}")
            return self.response(
                error={"detail": str(e)},
                message="Failed to generate revenue report",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def export(self, request):
        """
        GET /admin/reports/export/
        
        Export data in various formats:
        - users: Export user data
        - transactions: Export transaction data
        - revenue: Export revenue data
        
        Query params:
        - type: users, transactions, revenue
        - format: csv, json
        - start_date, end_date: Date range for filtering
        """
        try:
            export_type = request.query_params.get('type', 'transactions')
            format_type = request.query_params.get('format', 'csv')
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            
            if export_type == 'users':
                # Export user data
                query = supabase.table('profile').select('*')
                if start_date:
                    query = query.gte('created_at', start_date)
                if end_date:
                    query = query.lte('created_at', end_date)
                
                data_response = query.execute()
                data = data_response.data if data_response.data else []
                
                if format_type == 'csv':
                    response = HttpResponse(content_type='text/csv')
                    response['Content-Disposition'] = 'attachment; filename="users_export.csv"'
                    
                    if data:
                        writer = csv.DictWriter(response, fieldnames=data[0].keys())
                        writer.writeheader()
                        writer.writerows(data)
                    
                    return response
                
            elif export_type == 'transactions':
                # Export transaction data
                query = supabase.table('history').select('*')
                if start_date:
                    query = query.gte('created_at', start_date)
                if end_date:
                    query = query.lte('created_at', end_date)
                
                # Limit to prevent large exports
                data_response = query.limit(10000).execute()
                data = data_response.data if data_response.data else []
                
                if format_type == 'csv':
                    response = HttpResponse(content_type='text/csv')
                    response['Content-Disposition'] = 'attachment; filename="transactions_export.csv"'
                    
                    if data:
                        writer = csv.DictWriter(response, fieldnames=data[0].keys())
                        writer.writeheader()
                        writer.writerows(data)
                    
                    return response
            
            return self.response(
                data=data,
                message=f"{export_type.title()} data exported successfully",
                status_code=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.exception(f"Error in data export: {str(e)}")
            return self.response(
                error={"detail": str(e)},
                message="Failed to export data",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

@method_decorator(csrf_exempt, name='dispatch')
class AdminPushTokenView(APIView, ResponseMixin):
    """
    Push token management endpoints for admin operations
    """
    authentication_classes = [AdminSupabaseAuthentication]
    permission_classes = []
    
    def get(self, request):
        """
        GET /admin/push-tokens/
        
        Query params:
        - limit: Number of tokens to return (default: 50)
        - offset: Number of tokens to skip (default: 0)
        - user_id: Filter by specific user ID
        - active: Filter by active status (true/false)
        
        Returns paginated list of push tokens with user information
        """
        try:
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
        POST /admin/push-tokens/
        
        Create or update push tokens for a user
        
        Request body:
        {
            "user_id": "uuid",
            "token": "push_token",
            "active": true|false
        }
        """
        try:
            user_id = request.data.get('user_id')
            token = request.data.get('token')
            active = request.data.get('active', True)
            
            if not user_id or not token:
                return self.response(
                    error={"detail": "User ID and token are required"},
                    message="User ID and token are required",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            upsert_response = supabase.table('push_tokens').upsert({
                'user': user_id,
                'token': token,
                'active': active
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
class AdminNotificationsViewSet(ViewSet, ResponseMixin):
    """
    Push notification management endpoints for admin operations
    """
    authentication_classes = [AdminSupabaseAuthentication]
    permission_classes = []
    
    @action(detail=False, methods=['post'], url_path='send-push')
    def send_push(self, request):
        """
        POST /admin/notifications/send-push/
        
        Send push notifications to users:
        - Single user by user_id
        - Multiple users by user_ids list
        - All users (broadcast)
        - Users by role/criteria
        
        Request body:
        {
            "target_type": "single|multiple|broadcast|role",
            "user_id": "uuid",  // For single user
            "user_ids": ["uuid1", "uuid2"],  // For multiple users
            "role": "user|admin",  // For role-based targeting
            "title": "Notification title",
            "body": "Notification message",
            "data": {  // Optional custom data
                "action": "open_screen",
                "screen": "dashboard"
            },
            "priority": "normal|high",
            "sound": "default",
            "badge": 1
        }
        """
        try:
            target_type = request.data.get('target_type', 'single')
            title = request.data.get('title')
            body = request.data.get('body')
            data = request.data.get('data', {})
            badge = request.data.get('badge', 1)
            
            if not title or not body:
                return self.response(
                    error={"detail": "Title and body are required"},
                    message="Title and body are required",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            push_tokens = []
            
            if target_type == 'single':
                user_id = request.data.get('user_id')
                if not user_id:
                    return self.response(
                        error={"detail": "User ID is required for single user targeting"},
                        message="User ID is required",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
                
                tokens_response = supabase.table('push_tokens').select('token').eq('user', user_id).eq('active', True).execute()
                push_tokens = [token['token'] for token in tokens_response.data if tokens_response.data]
                
            elif target_type == 'multiple':
                user_ids = request.data.get('user_ids', [])
                if not user_ids:
                    return self.response(
                        error={"detail": "User IDs list is required for multiple user targeting"},
                        message="User IDs are required",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
                
                tokens_response = supabase.table('push_tokens').select('token').in_('user', user_ids).eq('active', True).execute()
                push_tokens = [token['token'] for token in tokens_response.data if tokens_response.data]
                
            elif target_type == 'broadcast':
                tokens_response = supabase.table('push_tokens').select('token').eq('active', True).execute()
                push_tokens = [token['token'] for token in tokens_response.data if tokens_response.data]
                
            elif target_type == 'role':
                role = request.data.get('role')
                if not role:
                    return self.response(
                        error={"detail": "Role is required for role-based targeting"},
                        message="Role is required",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
                
                users_response = supabase.table('profile').select('id').eq('role', role).execute()
                if users_response.data:
                    user_ids = [user['id'] for user in users_response.data]
                    tokens_response = supabase.table('push_tokens').select('token').in_('user', user_ids).eq('active', True).execute()
                    push_tokens = [token['token'] for token in tokens_response.data if tokens_response.data]
            
            if not push_tokens:
                return self.response(
                    error={"detail": "No active push tokens found for the specified target"},
                    message="No recipients found",
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            successful_sends = 0
            failed_sends = 0
            failed_tokens = []

            logger.info(f"Sending push notification to {len(push_tokens)} tokens. Target type: {target_type} with data: {data}.")
            
            ### Use bulk sending for efficiency - batch tokens into groups of 100
            batch_size = 100
            subtitle = request.data.get('subtitle', None)
            
            if len(push_tokens) <= batch_size:
                ### Single batch - use bulk sending
                try:
                    notifications = []
                    for token in push_tokens:
                        notification = {
                            "token": token,
                            "title": title,
                            "body": body,
                            "extra_data": data
                        }
                        if subtitle:
                            notification["subtitle"] = subtitle
                        notifications.append(notification)
                    
                    result = send_bulk_push_notifications(notifications)
                    
                    ### Process bulk result
                    if "data" in result:
                        for i, ticket in enumerate(result["data"]):
                            if ticket.get("status") == "ok":
                                successful_sends += 1
                            else:
                                failed_sends += 1
                                failed_tokens.append({
                                    "token": push_tokens[i], 
                                    "error": ticket.get("details", {}).get("error", "Unknown error")
                                })
                    else:
                        ### If no ticket data, assume all succeeded (fallback)
                        successful_sends = len(push_tokens)
                        
                except Exception as e:
                    logger.error(f"Bulk push notification failed: {str(e)}")
                    ### Fallback to individual sending
                    for token in push_tokens:
                        try:
                            send_push_notification(
                                token=token,
                                title=title,
                                body=body,
                                subtitle=subtitle,
                                extra_data=data,
                            )
                            successful_sends += 1
                        except Exception as individual_error:
                            failed_sends += 1
                            failed_tokens.append({"token": token, "error": str(individual_error)})
            else:
                # Multiple batches needed
                for i in range(0, len(push_tokens), batch_size):
                    batch_tokens = push_tokens[i:i + batch_size]
                    
                    try:
                        notifications = []
                        for token in batch_tokens:
                            notification = {
                                "token": token,
                                "title": title,
                                "body": body,
                                "extra_data": data
                            }
                            if subtitle:
                                notification["subtitle"] = subtitle
                            notifications.append(notification)
                        
                        result = send_bulk_push_notifications(notifications)
                        
                        # Process batch result
                        if "data" in result:
                            for j, ticket in enumerate(result["data"]):
                                if ticket.get("status") == "ok":
                                    successful_sends += 1
                                else:
                                    failed_sends += 1
                                    token_index = i + j
                                    if token_index < len(push_tokens):
                                        failed_tokens.append({
                                            "token": push_tokens[token_index], 
                                            "error": ticket.get("details", {}).get("error", "Unknown error")
                                        })
                        else:
                            # If no ticket data, assume all in batch succeeded
                            successful_sends += len(batch_tokens)
                            
                        logger.info(f"Batch {i//batch_size + 1}: Sent to {len(batch_tokens)} tokens")
                        
                    except Exception as batch_error:
                        logger.error(f"Batch {i//batch_size + 1} failed: {str(batch_error)}")
                        # Fallback to individual sending for this batch
                        for token in batch_tokens:
                            try:
                                send_push_notification(
                                    token=token,
                                    title=title,
                                    body=body,
                                    subtitle=subtitle,
                                    extra_data=data,
                                )
                                successful_sends += 1
                            except Exception as individual_error:
                                failed_sends += 1
                                failed_tokens.append({"token": token, "error": str(individual_error)})
            
            admin_user = getattr(request, 'user', None)
            admin_email = admin_user.email if admin_user else 'system'
            logger.info(f"Admin notification: {admin_email} sent '{title}' to {successful_sends} devices. Target type: {target_type}")
            
            result = {
                "target_type": target_type,
                "total_tokens": len(push_tokens),
                "successful_sends": successful_sends,
                "failed_sends": failed_sends,
                "failed_tokens": failed_tokens[:10],
                "notification": {
                    "title": title,
                    "body": body,
                    "data": data
                }
            }
            
            return self.response(
                data=result,
                message=f"Push notification sent to {successful_sends} out of {len(push_tokens)} devices",
                status_code=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.exception(f"Error in send push notification: {str(e)}")
            return self.response(
                error={"detail": str(e)},
                message="Failed to send push notification",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def tokens(self, request):
        """
        GET /admin/notifications/tokens/
        
        Get push token statistics and management
        
        Query params:
        - user_id: Get tokens for specific user
        - active: Filter by active status (true/false)
        - search: Search in token or user information
        - limit, offset: Pagination
        
        Returns push token information and statistics
        """
        try:
            user_id = request.query_params.get('user_id')
            active = request.query_params.get('active')
            search = request.query_params.get('search', '').strip()
            limit = int(request.query_params.get('limit', 50))
            offset = int(request.query_params.get('offset', 0))
            
            query = supabase.table('push_tokens').select('*, profile!inner(email, full_name)')
            
            if user_id:
                query = query.eq('user', user_id)
            
            if active is not None:
                query = query.eq('active', active.lower() == 'true')
            
            if search:
                search_terms = f"token.ilike.%{search}%,profile.email.ilike.%{search}%,profile.full_name.ilike.%{search}%"
                query = query.or_(search_terms)
            
            count_response = query.execute()
            total_count = len(count_response.data) if count_response.data else 0
            
            tokens_response = query.order('created_at', desc=True).range(
                offset, offset + limit - 1
            ).execute()
            
            stats_query = supabase.table('push_tokens').select('active')
            stats_response = stats_query.execute()
            
            active_count = 0
            inactive_count = 0
            if stats_response.data:
                active_count = len([token for token in stats_response.data if token.get('active')])
                inactive_count = len([token for token in stats_response.data if not token.get('active')])
                
            result = {
                "tokens": tokens_response.data if tokens_response.data else [],
                "statistics": {
                    "total_tokens": total_count,
                    "active_tokens": active_count,
                    "inactive_tokens": inactive_count
                },
            }


            return self.response(
                data=result,
                message="Push tokens retrieved successfully",
                status_code=status.HTTP_200_OK,
                count=total_count,
                next=offset + limit if offset + limit < total_count else None,
                previous=offset - limit if offset > 0 else None
            )
            
        except Exception as e:
            logger.exception(f"Error in get push tokens: {str(e)}")
            return self.response(
                error={"detail": str(e)},
                message="Failed to retrieve push tokens",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def test_notification(self, request):
        """
        POST /admin/notifications/test_notification/
        
        Send a test notification to admin's own device or specified test token
        
        Request body:
        {
            "token": "expo_push_token",  // Optional test token
            "title": "Test Notification",
            "body": "This is a test message"
        }
        """
        try:
            test_token = request.data.get('token')
            title = request.data.get('title', 'Test Notification')
            body = request.data.get('body', 'This is a test push notification from iSubscribe Admin')
            
            if not test_token:
                admin_user = getattr(request, 'user', None)
                if admin_user:
                    tokens_response = supabase.table('push_tokens').select('token').eq('user', admin_user.id).eq('active', True).limit(1).execute()
                    if tokens_response.data:
                        test_token = tokens_response.data[0]['token']
            
            if not test_token:
                return self.response(
                    error={"detail": "No test token available. Please provide a token or ensure you have an active push token."},
                    message="Test token required",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            notification_data = {
                "to": test_token,
                "title": title,
                "body": body,
                "data": {"test": True, "timestamp": datetime.now().isoformat()}
            }
            
            send_push(notification_data)
            
            return self.response(
                data={"token": test_token, "notification": notification_data},
                message="Test notification sent successfully",
                status_code=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.exception(f"Error in test notification: {str(e)}")
            return self.response(
                error={"detail": str(e)},
                message="Failed to send test notification",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )