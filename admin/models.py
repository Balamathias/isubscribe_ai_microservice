"""
Admin Models

This module contains model definitions for the admin app.
Since we're using Supabase for data storage, these models are primarily
for Django admin interface and documentation purposes.
"""

from django.db import models
from django.contrib.auth.models import AbstractUser


class AdminLog(models.Model):
    """
    Model to track admin actions for audit purposes
    """
    admin_user_id = models.CharField(max_length=255)
    admin_email = models.EmailField()
    action = models.CharField(max_length=100)
    target_user_id = models.CharField(max_length=255, null=True, blank=True)
    target_email = models.EmailField(null=True, blank=True)
    details = models.JSONField(default=dict)
    reason = models.TextField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'admin_logs'
        ordering = ['-created_at']
        verbose_name = 'Admin Log'
        verbose_name_plural = 'Admin Logs'
    
    def __str__(self):
        return f"{self.admin_email} - {self.action} - {self.created_at}"


class AdminSession(models.Model):
    """
    Model to track admin login sessions
    """
    admin_user_id = models.CharField(max_length=255)
    admin_email = models.EmailField()
    session_token = models.CharField(max_length=255, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    login_time = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    logout_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'admin_sessions'
        ordering = ['-login_time']
        verbose_name = 'Admin Session'
        verbose_name_plural = 'Admin Sessions'
    
    def __str__(self):
        return f"{self.admin_email} - {self.login_time}"


# Virtual models for Django admin interface (not stored in database)

class DashboardMetrics(models.Model):
    """
    Virtual model for dashboard metrics display in Django admin
    """
    total_users = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_transactions = models.IntegerField(default=0)
    success_rate = models.FloatField(default=0)
    generated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        managed = False  # This model is not stored in database
        verbose_name = 'Dashboard Metrics'
        verbose_name_plural = 'Dashboard Metrics'


class UserAnalytics(models.Model):
    """
    Virtual model for user analytics display in Django admin
    """
    period_days = models.IntegerField(default=30)
    new_users = models.IntegerField(default=0)
    active_users = models.IntegerField(default=0)
    growth_rate = models.FloatField(default=0)
    activity_rate = models.FloatField(default=0)
    generated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        managed = False  # This model is not stored in database
        verbose_name = 'User Analytics'
        verbose_name_plural = 'User Analytics'


class FinancialAnalytics(models.Model):
    """
    Virtual model for financial analytics display in Django admin
    """
    period_days = models.IntegerField(default=30)
    total_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_volume = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    average_transaction = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    success_rate = models.FloatField(default=0)
    generated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        managed = False  # This model is not stored in database
        verbose_name = 'Financial Analytics'
        verbose_name_plural = 'Financial Analytics'
