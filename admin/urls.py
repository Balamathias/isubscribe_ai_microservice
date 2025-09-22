"""
Admin URL Configuration

This module defines all URL patterns for the admin API endpoints.
All URLs are prefixed with /admin/ and require admin authentication.

Available endpoints:
- /admin/dashboard/ - Main dashboard overview
- /admin/analytics/ - Analytics endpoints
- /admin/system/ - System monitoring
- /admin/users/ - User management
- /admin/transactions/ - Transaction management
- /admin/reports/ - Report generation and exports
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AdminDashboardViewSet,
    AdminAnalyticsViewSet,
    AdminSystemViewSet,
    AdminUserManagementViewSet,
    AdminTransactionViewSet,
    AdminReportsViewSet,
    AdminPlansViewSet,
)

app_name = 'admin'

# Create router for ViewSets
router = DefaultRouter()
router.register(r'dashboard', AdminDashboardViewSet, basename='dashboard')
router.register(r'analytics', AdminAnalyticsViewSet, basename='analytics')
router.register(r'system', AdminSystemViewSet, basename='system')
router.register(r'users', AdminUserManagementViewSet, basename='users')
router.register(r'transactions', AdminTransactionViewSet, basename='transactions')
router.register(r'reports', AdminReportsViewSet, basename='reports'),
router.register(r'plans', AdminPlansViewSet, basename='plans'),

urlpatterns = [
    # Include all router URLs
    path('', include(router.urls)),
    
    # Additional custom endpoints can be added here
    # path('custom-endpoint/', CustomView.as_view(), name='custom-endpoint'),
    path('push-tokens/', AdminPushTokenView.as_view(), name='push-tokens'),
]

"""
URL Patterns Documentation:

Dashboard Endpoints:
- GET /admin/dashboard/ - Main dashboard overview with key metrics

Analytics Endpoints:
- GET /admin/analytics/users/ - User analytics and insights
- GET /admin/analytics/financial/ - Financial analytics and revenue
- GET /admin/analytics/transactions/ - Transaction monitoring and analysis
- GET /admin/analytics/services/ - Service performance analytics

System Endpoints:
- GET /admin/system/health/ - System health monitoring

User Management Endpoints:
- GET /admin/users/ - List users with search and filtering
- GET /admin/users/{id}/ - Get detailed user information
- POST /admin/users/{id}/actions/ - Perform admin actions on users

Transaction Management Endpoints:
- GET /admin/transactions/ - Advanced transaction search and filtering

Report Endpoints:
- GET /admin/reports/revenue/ - Generate revenue reports
- GET /admin/reports/export/ - Export data in various formats

Query Parameters:

Common parameters:
- limit: Number of records to return (default varies by endpoint)
- offset: Number of records to skip for pagination
- days: Number of days to analyze (default: 30)
- start_date: Start date in ISO format
- end_date: End date in ISO format

User list parameters:
- search: Search term for email, name, or phone
- role: Filter by user role
- created_after: Filter users created after date
- created_before: Filter users created before date

Transaction list parameters:
- search: Search in description, email, transaction_id
- status: Filter by transaction status (successful, failed, pending)
- type: Filter by transaction type (data_bundle, airtime, electricity, etc.)
- provider: Filter by provider
- amount_min, amount_max: Amount range filter
- user_id: Filter by specific user

Report parameters:
- period: daily, weekly, monthly (for revenue reports)
- format: json, csv (for export)
- type: users, transactions, revenue (for export)

Response Format:
All endpoints follow the ResponseMixin pattern:
{
    "success": true,
    "message": "Description of the operation",
    "data": { ... },
    "error": null,
    "count": 100,  // For paginated responses
    "next": 50,    // Next offset for pagination
    "previous": 0  // Previous offset for pagination
}

Authentication:
All endpoints require admin authentication using the AdminSupabaseAuthentication class.
Users must have 'admin' or 'super_admin' role in their profile.

Permissions:
- IsAdminUser: Basic admin access (admin or super_admin role)
- IsSuperAdminUser: Super admin only access
- CanViewAnalytics: Permission to view analytics (admin or super_admin)
- CanModifyUsers: Permission to modify users (super_admin only)
- CanViewFinancials: Permission to view financial data (admin or super_admin)
"""
