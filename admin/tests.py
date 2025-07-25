"""
Admin App Tests

This module contains comprehensive tests for the admin functionality
including authentication, permissions, analytics, and API endpoints.
"""

from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from admin.services import (
    UserAnalyticsService,
    FinancialAnalyticsService,
    TransactionAnalyticsService,
    ServiceAnalyticsService,
    SystemHealthService
)
from admin.permissions import IsAdminUser, AdminUser


class AdminServicesTestCase(TestCase):
    """Test cases for admin services"""
    
    def setUp(self):
        self.mock_supabase_response = Mock()
        self.mock_supabase_response.data = [
            {
                'id': '123',
                'email': 'test@example.com',
                'created_at': '2024-01-01T00:00:00Z',
                'amount': 1000,
                'commission': 50,
                'status': 'successful',
                'type': 'data_bundle'
            }
        ]
        self.mock_supabase_response.count = 1
    
    @patch('admin.services.supabase')
    def test_user_analytics_overview(self, mock_supabase):
        """Test user analytics overview functionality"""
        mock_supabase.table.return_value.select.return_value.execute.return_value = self.mock_supabase_response
        mock_supabase.table.return_value.select.return_value.gte.return_value.execute.return_value = self.mock_supabase_response
        
        result = UserAnalyticsService.get_user_overview(30)
        
        self.assertIsInstance(result, dict)
        self.assertIn('total_users', result)
        self.assertIn('new_users', result)
        self.assertIn('active_users', result)
    
    @patch('admin.services.supabase')
    def test_financial_analytics(self, mock_supabase):
        """Test financial analytics functionality"""
        mock_supabase.table.return_value.select.return_value.gte.return_value.lte.return_value.execute.return_value = self.mock_supabase_response
        
        result = FinancialAnalyticsService.get_revenue_overview(days=30)
        
        self.assertIsInstance(result, dict)
        self.assertIn('total_revenue', result)
        self.assertIn('total_volume', result)
        self.assertIn('transaction_count', result)
    
    @patch('admin.services.supabase')
    def test_transaction_analytics(self, mock_supabase):
        """Test transaction analytics functionality"""
        mock_supabase.table.return_value.select.return_value.gte.return_value.execute.return_value = self.mock_supabase_response
        
        result = TransactionAnalyticsService.get_transaction_overview(30)
        
        self.assertIsInstance(result, dict)
        self.assertIn('total_transactions', result)
        self.assertIn('success_rate', result)
        self.assertIn('transaction_types', result)
    
    @patch('admin.services.supabase')
    def test_system_health(self, mock_supabase):
        """Test system health monitoring"""
        mock_supabase.table.return_value.select.return_value.limit.return_value.execute.return_value = self.mock_supabase_response
        
        result = SystemHealthService.get_system_health()
        
        self.assertIsInstance(result, dict)
        self.assertIn('overall_status', result)
        self.assertIn('database_health', result)


class AdminPermissionsTestCase(TestCase):
    """Test cases for admin permissions"""
    
    def setUp(self):
        self.admin_user = AdminUser({
            'id': '123',
            'email': 'admin@example.com',
            'role': 'admin'
        })
        
        self.super_admin_user = AdminUser({
            'id': '456',
            'email': 'superadmin@example.com',
            'role': 'super_admin'
        })
        
        self.regular_user = AdminUser({
            'id': '789',
            'email': 'user@example.com',
            'role': 'user'
        })
    
    def test_admin_user_creation(self):
        """Test AdminUser class functionality"""
        self.assertTrue(self.admin_user.is_admin)
        self.assertFalse(self.admin_user.is_super_admin)
        self.assertTrue(self.super_admin_user.is_super_admin)
        self.assertFalse(self.regular_user.is_admin)
    
    def test_is_admin_permission(self):
        """Test IsAdminUser permission class"""
        permission = IsAdminUser()
        
        # Mock request objects
        admin_request = Mock()
        admin_request.user = self.admin_user
        
        regular_request = Mock()
        regular_request.user = self.regular_user
        
        self.assertTrue(permission.has_permission(admin_request, None))
        self.assertFalse(permission.has_permission(regular_request, None))


class AdminAPITestCase(APITestCase):
    """Test cases for admin API endpoints"""
    
    def setUp(self):
        # Mock authentication for tests
        self.admin_user = AdminUser({
            'id': '123',
            'email': 'admin@example.com',
            'role': 'admin'
        })
    
    @patch('admin.views.AdminSupabaseAuthentication.authenticate')
    @patch('admin.services.UserAnalyticsService.get_user_overview')
    @patch('admin.services.FinancialAnalyticsService.get_revenue_overview')
    @patch('admin.services.TransactionAnalyticsService.get_transaction_overview')
    @patch('admin.services.SystemHealthService.get_system_health')
    def test_dashboard_endpoint(self, mock_health, mock_transactions, mock_financial, mock_users, mock_auth):
        """Test admin dashboard endpoint"""
        # Mock authentication
        mock_auth.return_value = (self.admin_user, 'mock_token')
        
        # Mock service responses
        mock_users.return_value = {'total_users': 100, 'new_users': 10}
        mock_financial.return_value = {'total_revenue': 5000, 'total_volume': 50000}
        mock_transactions.return_value = {'total_transactions': 200, 'success_rate': 95}
        mock_health.return_value = {'overall_status': 'healthy'}
        
        response = self.client.get('/admin/dashboard/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('overview', response.data['data'])
        self.assertIn('user_metrics', response.data['data'])
        self.assertIn('financial_metrics', response.data['data'])
    
    @patch('admin.views.AdminSupabaseAuthentication.authenticate')
    @patch('admin.services.UserAnalyticsService.get_user_overview')
    def test_user_analytics_endpoint(self, mock_service, mock_auth):
        """Test user analytics endpoint"""
        mock_auth.return_value = (self.admin_user, 'mock_token')
        mock_service.return_value = {
            'total_users': 100,
            'new_users': 10,
            'active_users': 80,
            'growth_rate': 5.5
        }
        
        response = self.client.get('/admin/analytics/users/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_users', response.data['data'])
        self.assertEqual(response.data['data']['total_users'], 100)
    
    @patch('admin.views.AdminSupabaseAuthentication.authenticate')
    @patch('admin.services.FinancialAnalyticsService.get_revenue_overview')
    def test_financial_analytics_endpoint(self, mock_service, mock_auth):
        """Test financial analytics endpoint"""
        mock_auth.return_value = (self.admin_user, 'mock_token')
        mock_service.return_value = {
            'total_revenue': 10000,
            'total_volume': 100000,
            'success_rate': 95.5
        }
        
        response = self.client.get('/admin/analytics/financial/?days=30')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_revenue', response.data['data'])
        self.assertEqual(response.data['data']['total_revenue'], 10000)
    
    @patch('admin.views.AdminSupabaseAuthentication.authenticate')
    @patch('admin.services.SystemHealthService.get_system_health')
    def test_system_health_endpoint(self, mock_service, mock_auth):
        """Test system health endpoint"""
        mock_auth.return_value = (self.admin_user, 'mock_token')
        mock_service.return_value = {
            'overall_status': 'healthy',
            'database_health': {'status': 'healthy'},
            'service_health': {'status': 'healthy'}
        }
        
        response = self.client.get('/admin/system/health/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['overall_status'], 'healthy')
    
    def test_unauthenticated_access(self):
        """Test that unauthenticated requests are rejected"""
        response = self.client.get('/admin/dashboard/')
        
        # Should return 401 or 403 depending on authentication setup
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])


class AdminDataExportTestCase(APITestCase):
    """Test cases for data export functionality"""
    
    def setUp(self):
        self.admin_user = AdminUser({
            'id': '123',
            'email': 'admin@example.com',
            'role': 'admin'
        })
    
    @patch('admin.views.AdminSupabaseAuthentication.authenticate')
    @patch('admin.services.supabase')
    def test_csv_export(self, mock_supabase, mock_auth):
        """Test CSV export functionality"""
        mock_auth.return_value = (self.admin_user, 'mock_token')
        
        # Mock supabase response
        mock_response = Mock()
        mock_response.data = [
            {'id': 1, 'email': 'test@example.com', 'created_at': '2024-01-01'},
            {'id': 2, 'email': 'test2@example.com', 'created_at': '2024-01-02'}
        ]
        mock_supabase.table.return_value.select.return_value.execute.return_value = mock_response
        
        response = self.client.get('/admin/reports/export/?type=users&format=csv')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment', response['Content-Disposition'])


if __name__ == '__main__':
    import unittest
    unittest.main()
