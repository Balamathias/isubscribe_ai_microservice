"""
Admin Permissions and Authentication

This module provides custom permission classes for admin functionality
ensuring only authorized users can access admin endpoints.
"""

from rest_framework.permissions import BasePermission
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.models import AnonymousUser
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)


class AdminUser:
    """Custom user class for admin users"""
    
    def __init__(self, user_data: dict):
        self.id = user_data.get('id')
        self.email = user_data.get('email')
        self.full_name = user_data.get('full_name')
        self.role = user_data.get('role', 'user')
        self.is_authenticated = True
        self.is_admin = self.role in ['admin', 'super_admin']
        self.is_super_admin = self.role == 'super_admin'
    
    def __str__(self):
        return f"AdminUser({self.email})"


class IsAdminUser(BasePermission):
    """
    Permission class to allow access only to admin users.
    Checks if the user has admin or super_admin role.
    """
    
    def has_permission(self, request, view):
        if not request.user or not hasattr(request.user, 'is_authenticated'):
            return False
            
        if not request.user.is_authenticated:
            return False
            
        # Check if user has admin role
        return hasattr(request.user, 'is_admin') and request.user.is_admin
    
    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class IsSuperAdminUser(BasePermission):
    """
    Permission class to allow access only to super admin users.
    """
    
    def has_permission(self, request, view):
        if not request.user or not hasattr(request.user, 'is_authenticated'):
            return False
            
        if not request.user.is_authenticated:
            return False
            
        # Check if user has super admin role
        return hasattr(request.user, 'is_super_admin') and request.user.is_super_admin
    
    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class CanViewAnalytics(BasePermission):
    """
    Permission to view analytics data.
    Allows admin and super_admin users.
    """
    
    def has_permission(self, request, view):
        if not request.user or not hasattr(request.user, 'is_authenticated'):
            return False
            
        if not request.user.is_authenticated:
            return False
            
        return hasattr(request.user, 'is_admin') and request.user.is_admin


class CanModifyUsers(BasePermission):
    """
    Permission to modify user accounts.
    Only allows super_admin users for safety.
    """
    
    def has_permission(self, request, view):
        if not request.user or not hasattr(request.user, 'is_authenticated'):
            return False
            
        if not request.user.is_authenticated:
            return False
            
        # Only super admins can modify users
        return hasattr(request.user, 'is_super_admin') and request.user.is_super_admin


class CanViewFinancials(BasePermission):
    """
    Permission to view financial data.
    Allows admin and super_admin users.
    """
    
    def has_permission(self, request, view):
        if not request.user or not hasattr(request.user, 'is_authenticated'):
            return False
            
        if not request.user.is_authenticated:
            return False
            
        return hasattr(request.user, 'is_admin') and request.user.is_admin


class AdminSupabaseAuthentication(BaseAuthentication):
    """
    Custom authentication class for admin users using Supabase.
    Extends the base Supabase authentication to check for admin roles.
    """
    
    def authenticate(self, request):
        from auth.supabase import SupabaseAuthentication
        
        try:
            # Use the base Supabase authentication
            base_auth = SupabaseAuthentication()
            auth_result = base_auth.authenticate(request)
            
            if not auth_result:
                return None
                
            user, token = auth_result
            
            # Check if user has admin role
            if not hasattr(user, 'role') or user.role not in ['admin', 'super_admin']:
                raise AuthenticationFailed('Admin access required')
            
            # Create admin user instance
            admin_user = AdminUser({
                'id': user.id,
                'email': user.email,
                'full_name': getattr(user, 'full_name', user.email),
                'role': user.role
            })
            
            return (admin_user, token)
            
        except Exception as e:
            logger.error(f"Admin authentication error: {str(e)}")
            raise AuthenticationFailed('Authentication failed')
    
    def authenticate_header(self, request):
        return 'Bearer'
