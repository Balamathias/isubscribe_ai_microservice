"""
Admin Services for iSubscribe Platform

This module provides comprehensive analytics and management services
for the iSubscribe telecom platform admin dashboard.
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from django.db.models import Count, Sum, Avg, Q
from services.supabase import superbase as supabase
import logging

logger = logging.getLogger(__name__)


class UserAnalyticsService:
    """Service for user-related analytics and insights"""
    
    @staticmethod
    def get_user_overview(days: int = 30) -> Dict[str, Any]:
        """
        Get comprehensive user overview including growth metrics
        
        Args:
            days: Number of days to analyze (default: 30)
            
        Returns:
            Dict containing user metrics and analytics
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Total users
            total_users_response = supabase.table('profile').select('id', count='exact').execute()
            total_users = total_users_response.count or 0
            
            # New registrations in the period
            new_users_response = supabase.table('profile').select('*').gte(
                'created_at', start_date.isoformat()
            ).execute()
            new_users = len(new_users_response.data) if new_users_response.data else 0
            
            # Active users (users with transactions in the period)
            active_users_response = supabase.table('history').select('user').gte(
                'created_at', start_date.isoformat()
            ).execute()
            
            unique_active_users = len(set(tx['user'] for tx in active_users_response.data if tx.get('user'))) if active_users_response.data else 0
            
            # Users with wallets
            wallet_users_response = supabase.table('wallet').select('user', count='exact').execute()
            wallet_users = wallet_users_response.count or 0
            
            # Daily registration breakdown
            daily_registrations = UserAnalyticsService._get_daily_registrations(start_date, end_date)
            
            # User states distribution
            states_response = supabase.table('profile').select('state').execute()
            states_data = [user.get('state') for user in states_response.data if user.get('state')]
            states_distribution = pd.Series(states_data).value_counts().head(10).to_dict()
            
            return {
                "total_users": total_users,
                "new_users": new_users,
                "active_users": unique_active_users,
                "wallet_users": wallet_users,
                "activity_rate": round((unique_active_users / total_users * 100) if total_users > 0 else 0, 2),
                "growth_rate": round((new_users / (total_users - new_users) * 100) if (total_users - new_users) > 0 else 0, 2),
                "daily_registrations": daily_registrations,
                "top_states": states_distribution,
                "period_days": days
            }
            
        except Exception as e:
            logger.error(f"Error in get_user_overview: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    def _get_daily_registrations(start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get daily registration breakdown"""
        try:
            registrations_response = supabase.table('profile').select('created_at').gte(
                'created_at', start_date.isoformat()
            ).lte('created_at', end_date.isoformat()).execute()
            
            if not registrations_response.data:
                return []
            
            df = pd.DataFrame(registrations_response.data)
            df['created_at'] = pd.to_datetime(df['created_at'])
            df['date'] = df['created_at'].dt.date
            
            daily_counts = df.groupby('date').size().reset_index(name='count')
            
            return [
                {
                    "date": row['date'].isoformat(),
                    "count": int(row['count'])
                }
                for _, row in daily_counts.iterrows()
            ]
            
        except Exception as e:
            logger.error(f"Error in _get_daily_registrations: {str(e)}")
            return []

    @staticmethod
    def get_user_engagement_metrics(days: int = 30) -> Dict[str, Any]:
        """Get user engagement and retention metrics"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Repeat customers (users with multiple transactions)
            repeat_customers_response = supabase.rpc('get_repeat_customers', {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }).execute()
            
            # High frequency users (potential suspicious activity)
            high_freq_response = supabase.rpc('get_high_frequency_users', {
                'time_window': '1 hour',
                'min_transactions': 10
            }).execute()
            
            # Most active users from recent transactions
            active_users_response = supabase.table('history').select('user, email').gte(
                'created_at', start_date.isoformat()
            ).execute()
            
            if active_users_response.data:
                user_activity = pd.DataFrame(active_users_response.data)
                top_users = user_activity['user'].value_counts().head(10).to_dict()
            else:
                top_users = {}
            
            # Transaction frequency analysis
            frequency_analysis = UserAnalyticsService._analyze_transaction_frequency(start_date, end_date)
            
            return {
                "repeat_customers": repeat_customers_response.data if repeat_customers_response.data else [],
                "repeat_customers_count": len(repeat_customers_response.data) if repeat_customers_response.data else 0,
                "high_frequency_users": high_freq_response.data if high_freq_response.data else [],
                "top_active_users": top_users,
                "frequency_analysis": frequency_analysis,
                "period_days": days
            }
            
        except Exception as e:
            logger.error(f"Error in get_user_engagement_metrics: {str(e)}")
            return {"error": str(e)}

    @staticmethod
    def _analyze_transaction_frequency(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Analyze transaction frequency patterns"""
        try:
            transactions_response = supabase.table('history').select('user, created_at').gte(
                'created_at', start_date.isoformat()
            ).lte('created_at', end_date.isoformat()).execute()
            
            if not transactions_response.data:
                return {}
            
            df = pd.DataFrame(transactions_response.data)
            user_transaction_counts = df['user'].value_counts()
            
            frequency_ranges = {
                "1_transaction": len(user_transaction_counts[user_transaction_counts == 1]),
                "2_5_transactions": len(user_transaction_counts[(user_transaction_counts >= 2) & (user_transaction_counts <= 5)]),
                "6_10_transactions": len(user_transaction_counts[(user_transaction_counts >= 6) & (user_transaction_counts <= 10)]),
                "10_plus_transactions": len(user_transaction_counts[user_transaction_counts > 10])
            }
            
            return frequency_ranges
            
        except Exception as e:
            logger.error(f"Error in _analyze_transaction_frequency: {str(e)}")
            return {}


class FinancialAnalyticsService:
    """Service for financial analytics and revenue insights"""
    
    @staticmethod
    def get_revenue_overview(start_date: str = None, end_date: str = None, days: int = 30) -> Dict[str, Any]:
        """
        Get comprehensive revenue overview and analytics
        
        Args:
            start_date: Start date in ISO format (optional)
            end_date: End date in ISO format (optional) 
            days: Number of days to analyze if dates not provided
            
        Returns:
            Dict containing revenue metrics and analytics
        """
        try:
            if not start_date or not end_date:
                end_dt = datetime.now()
                start_dt = end_dt - timedelta(days=days)
                start_date = start_dt.isoformat()
                end_date = end_dt.isoformat()
            
            # Get all transactions in the period
            transactions_response = supabase.table('history').select(
                'amount, commission, type, provider, status, created_at, user'
            ).gte('created_at', start_date).lte('created_at', end_date).execute()
            
            if not transactions_response.data:
                return {
                    "total_revenue": 0,
                    "total_volume": 0,
                    "transaction_count": 0,
                    "average_transaction": 0,
                    "success_rate": 0,
                    "revenue_by_service": {},
                    "revenue_by_provider": {},
                    "daily_trends": [],
                    "period_start": start_date,
                    "period_end": end_date
                }
            
            df = pd.DataFrame(transactions_response.data)
            
            # Convert numeric columns
            df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)
            df['commission'] = pd.to_numeric(df['commission'], errors='coerce').fillna(0)
            
            # Filter successful transactions for revenue calculations
            successful_transactions = df[df['status'] == 'success']
            
            # Basic metrics
            total_revenue = successful_transactions['commission'].sum()
            total_volume = successful_transactions['amount'].sum()
            transaction_count = len(df)
            successful_count = len(successful_transactions)
            success_rate = (successful_count / transaction_count * 100) if transaction_count > 0 else 0
            avg_transaction = successful_transactions['amount'].mean() if len(successful_transactions) > 0 else 0
            
            # Revenue by service type
            revenue_by_service = successful_transactions.groupby('type')['commission'].sum().to_dict()
            
            # Revenue by provider
            revenue_by_provider = successful_transactions.groupby('provider')['commission'].sum().to_dict()
            
            # Daily trends
            daily_trends = FinancialAnalyticsService._get_daily_revenue_trends(successful_transactions)
            
            # Get wallet analytics
            wallet_analytics = FinancialAnalyticsService._get_wallet_analytics()
            
            return {
                "total_revenue": float(total_revenue),
                "total_volume": float(total_volume),
                "transaction_count": transaction_count,
                "successful_transactions": successful_count,
                "failed_transactions": transaction_count - successful_count,
                "success_rate": round(success_rate, 2),
                "average_transaction": round(float(avg_transaction), 2),
                "revenue_by_service": {k: float(v) for k, v in revenue_by_service.items()},
                "revenue_by_provider": {k: float(v) for k, v in revenue_by_provider.items()},
                "daily_trends": daily_trends,
                "wallet_analytics": wallet_analytics,
                "period_start": start_date,
                "period_end": end_date
            }
            
        except Exception as e:
            logger.error(f"Error in get_revenue_overview: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    def _get_daily_revenue_trends(df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Get daily revenue trends"""
        try:
            if df.empty:
                return []
                
            df['created_at'] = pd.to_datetime(df['created_at'])
            df['date'] = df['created_at'].dt.date
            
            daily_stats = df.groupby('date').agg({
                'commission': 'sum',
                'amount': 'sum',
                'type': 'count'
            }).reset_index()
            
            daily_stats.columns = ['date', 'revenue', 'volume', 'transactions']
            
            return [
                {
                    "date": row['date'].isoformat(),
                    "revenue": float(row['revenue']),
                    "volume": float(row['volume']),
                    "transactions": int(row['transactions'])
                }
                for _, row in daily_stats.iterrows()
            ]
            
        except Exception as e:
            logger.error(f"Error in _get_daily_revenue_trends: {str(e)}")
            return []
    
    @staticmethod
    def _get_wallet_analytics() -> Dict[str, Any]:
        """Get wallet-related analytics"""
        try:
            wallets_response = supabase.table('wallet').select('balance, cashback_balance').execute()
            
            if not wallets_response.data:
                return {}
            
            df = pd.DataFrame(wallets_response.data)
            df['balance'] = pd.to_numeric(df['balance'], errors='coerce').fillna(0)
            df['cashback_balance'] = pd.to_numeric(df['cashback_balance'], errors='coerce').fillna(0)
            
            return {
                "total_wallet_balance": float(df['balance'].sum()),
                "total_cashback_balance": float(df['cashback_balance'].sum()),
                "average_wallet_balance": round(float(df['balance'].mean()), 2),
                "users_with_zero_balance": len(df[df['balance'] == 0]),
                "users_with_positive_balance": len(df[df['balance'] > 0]),
                "highest_balance": float(df['balance'].max()),
                "balance_distribution": {
                    "min": float(df['balance'].min()),
                    "max": float(df['balance'].max()),
                    "median": float(df['balance'].median()),
                    "std": float(df['balance'].std()) if len(df) > 1 else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error in _get_wallet_analytics: {str(e)}")
            return {}


class TransactionAnalyticsService:
    """Service for transaction monitoring and analysis"""
    
    @staticmethod
    def get_transaction_overview(days: int = 30) -> Dict[str, Any]:
        """Get comprehensive transaction overview"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Get all transactions
            transactions_response = supabase.table('history').select('*').gte(
                'created_at', start_date.isoformat()
            ).execute()
            
            if not transactions_response.data:
                return {
                    "total_transactions": 0,
                    "successful_transactions": 0,
                    "failed_transactions": 0,
                    "pending_transactions": 0,
                    "success_rate": 0,
                    "failure_rate": 0,
                    "transaction_types": {},
                    "provider_performance": {},
                    "hourly_patterns": {},
                    "period_days": days
                }
            
            df = pd.DataFrame(transactions_response.data)
            
            # Status distribution
            status_counts = df['status'].value_counts().to_dict()
            total_transactions = len(df)
            successful = status_counts.get('success', 0)
            failed = status_counts.get('failed', 0)
            pending = status_counts.get('pending', 0)
            
            # Success and failure rates
            success_rate = (successful / total_transactions * 100) if total_transactions > 0 else 0
            failure_rate = (failed / total_transactions * 100) if total_transactions > 0 else 0
            
            # Transaction types
            type_counts = df['type'].value_counts().to_dict()
            
            # Provider performance
            provider_performance = TransactionAnalyticsService._analyze_provider_performance(df)
            
            # Hourly patterns
            hourly_patterns = TransactionAnalyticsService._analyze_hourly_patterns(df)
            
            # Suspicious activities
            suspicious_activities = TransactionAnalyticsService.detect_suspicious_activities(days)
            
            return {
                "total_transactions": total_transactions,
                "successful_transactions": successful,
                "failed_transactions": failed,
                "pending_transactions": pending,
                "success_rate": round(success_rate, 2),
                "failure_rate": round(failure_rate, 2),
                "transaction_types": type_counts,
                "provider_performance": provider_performance,
                "hourly_patterns": hourly_patterns,
                "suspicious_activities": suspicious_activities,
                "status_distribution": status_counts,
                "period_days": days
            }
            
        except Exception as e:
            logger.error(f"Error in get_transaction_overview: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    def _analyze_provider_performance(df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze performance by provider"""
        try:
            if df.empty:
                return {}
            
            provider_stats = df.groupby('provider').agg({
                'status': ['count', lambda x: (x == 'success').sum(), lambda x: (x == 'failed').sum()],
                'amount': 'sum',
                'commission': 'sum'
            }).round(2)
            
            provider_stats.columns = ['total_transactions', 'success', 'failed', 'total_volume', 'total_commission']
            provider_stats['success_rate'] = (provider_stats['success'] / provider_stats['total_transactions'] * 100).round(2)
            
            return provider_stats.to_dict('index')
            
        except Exception as e:
            logger.error(f"Error in _analyze_provider_performance: {str(e)}")
            return {}
    
    @staticmethod
    def _analyze_hourly_patterns(df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze transaction patterns by hour"""
        try:
            if df.empty:
                return {}
            
            df['created_at'] = pd.to_datetime(df['created_at'])
            df['hour'] = df['created_at'].dt.hour
            
            hourly_counts = df.groupby('hour').size().to_dict()
            
            # Fill missing hours with 0
            hourly_pattern = {str(hour): hourly_counts.get(hour, 0) for hour in range(24)}
            
            return hourly_pattern
            
        except Exception as e:
            logger.error(f"Error in _analyze_hourly_patterns: {str(e)}")
            return {}
    
    @staticmethod
    def detect_suspicious_activities(days: int = 1) -> Dict[str, Any]:
        """Detect potentially suspicious transaction activities"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # High frequency users (more than 20 transactions in the period)
            high_freq_response = supabase.table('history').select('user, email').gte(
                'created_at', start_date.isoformat()
            ).execute()
            
            if high_freq_response.data:
                user_counts = pd.Series([tx['user'] for tx in high_freq_response.data]).value_counts()
                high_freq_users = user_counts[user_counts > 20].to_dict()
            else:
                high_freq_users = {}
            
            # Large transactions (above 100,000)
            large_transactions_response = supabase.table('history').select(
                'id, user, amount, type, created_at, email'
            ).gt('amount', 100000).gte('created_at', start_date.isoformat()).execute()
            
            # Multiple failed transactions from same user
            failed_transactions_response = supabase.table('history').select('user, email').eq(
                'status', 'failed'
            ).gte('created_at', start_date.isoformat()).execute()
            
            if failed_transactions_response.data:
                failed_user_counts = pd.Series([tx['user'] for tx in failed_transactions_response.data]).value_counts()
                multiple_failures = failed_user_counts[failed_user_counts > 5].to_dict()
            else:
                multiple_failures = {}
            
            return {
                "high_frequency_users": dict(list(high_freq_users.items())[:10]),  # Top 10
                "large_transactions": large_transactions_response.data[:20] if large_transactions_response.data else [],  # Top 20
                "multiple_failures": dict(list(multiple_failures.items())[:10]),  # Top 10
                "total_suspicious_patterns": len(high_freq_users) + len(large_transactions_response.data or []) + len(multiple_failures)
            }
            
        except Exception as e:
            logger.error(f"Error in detect_suspicious_activities: {str(e)}")
            return {"error": str(e)}


class ServiceAnalyticsService:
    """Service for analyzing different service performance"""
    
    @staticmethod
    def get_service_performance(days: int = 30) -> Dict[str, Any]:
        """Get performance analytics for all services"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Data bundle analytics
            data_analytics = ServiceAnalyticsService._get_data_service_analytics(start_date, end_date)
            
            # Airtime analytics
            airtime_analytics = ServiceAnalyticsService._get_airtime_analytics(start_date, end_date)
            
            # Bill payment analytics
            bills_analytics = ServiceAnalyticsService._get_bills_analytics(start_date, end_date)
            
            # Education services analytics
            education_analytics = ServiceAnalyticsService._get_education_analytics(start_date, end_date)
            
            return {
                "data_services": data_analytics,
                "airtime_services": airtime_analytics,
                "bill_payments": bills_analytics,
                "education_services": education_analytics,
                "period_days": days
            }
            
        except Exception as e:
            logger.error(f"Error in get_service_performance: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    def _get_data_service_analytics(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Analyze data bundle service performance"""
        try:
            # Get data transactions
            data_transactions = supabase.table('history').select(
                'amount, commission, provider, status'
            ).eq('type', 'data_topup').gte(
                'created_at', start_date.isoformat()
            ).lte('created_at', end_date.isoformat()).execute()
            
            if not data_transactions.data:
                return {"total_transactions": 0, "revenue": 0, "volume": 0}
            
            df = pd.DataFrame(data_transactions.data)
            df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)
            df['commission'] = pd.to_numeric(df['commission'], errors='coerce').fillna(0)
            
            successful_df = df[df['status'] == 'success']
            
            # Provider breakdown
            provider_stats = successful_df.groupby('provider').agg({
                'amount': 'sum',
                'commission': 'sum',
                'status': 'count'
            }).to_dict('index')
            
            return {
                "total_transactions": len(df),
                "successful_transactions": len(successful_df),
                "revenue": float(successful_df['commission'].sum()),
                "volume": float(successful_df['amount'].sum()),
                "provider_breakdown": provider_stats,
                "success_rate": round(len(successful_df) / len(df) * 100, 2) if len(df) > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error in _get_data_service_analytics: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    def _get_airtime_analytics(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Analyze airtime service performance"""
        try:
            airtime_transactions = supabase.table('history').select(
                'amount, commission, provider, status'
            ).eq('type', 'airtime_topup').gte(
                'created_at', start_date.isoformat()
            ).lte('created_at', end_date.isoformat()).execute()
            
            if not airtime_transactions.data:
                return {"total_transactions": 0, "revenue": 0, "volume": 0}
            
            df = pd.DataFrame(airtime_transactions.data)
            df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)
            df['commission'] = pd.to_numeric(df['commission'], errors='coerce').fillna(0)
            
            successful_df = df[df['status'] == 'success']
            
            return {
                "total_transactions": len(df),
                "successful_transactions": len(successful_df),
                "revenue": float(successful_df['commission'].sum()),
                "volume": float(successful_df['amount'].sum()),
                "success_rate": round(len(successful_df) / len(df) * 100, 2) if len(df) > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error in _get_airtime_analytics: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    def _get_bills_analytics(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Analyze bill payment service performance"""
        try:
            bills_transactions = supabase.table('history').select(
                'amount, commission, provider, status, type'
            ).filter('type', 'in', '(electricity,tv,cable)').gte(
                'created_at', start_date.isoformat()
            ).lte('created_at', end_date.isoformat()).execute()
            
            if not bills_transactions.data:
                return {"total_transactions": 0, "revenue": 0, "volume": 0}
            
            df = pd.DataFrame(bills_transactions.data)
            df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)
            df['commission'] = pd.to_numeric(df['commission'], errors='coerce').fillna(0)
            
            successful_df = df[df['status'] == 'success']
            
            # Breakdown by bill type
            type_breakdown = successful_df.groupby('type').agg({
                'amount': 'sum',
                'commission': 'sum',
                'status': 'count'
            }).to_dict('index')
            
            return {
                "total_transactions": len(df),
                "successful_transactions": len(successful_df),
                "revenue": float(successful_df['commission'].sum()),
                "volume": float(successful_df['amount'].sum()),
                "type_breakdown": type_breakdown,
                "success_rate": round(len(successful_df) / len(df) * 100, 2) if len(df) > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error in _get_bills_analytics: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    def _get_education_analytics(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Analyze education service performance"""
        try:
            education_transactions = supabase.table('history').select(
                'amount, commission, provider, status, type'
            ).filter('type', 'in', '(jamb,waec,education)').gte(
                'created_at', start_date.isoformat()
            ).lte('created_at', end_date.isoformat()).execute()
            
            if not education_transactions.data:
                return {"total_transactions": 0, "revenue": 0, "volume": 0}
            
            df = pd.DataFrame(education_transactions.data)
            df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)
            df['commission'] = pd.to_numeric(df['commission'], errors='coerce').fillna(0)
            
            successful_df = df[df['status'] == 'success']
            
            return {
                "total_transactions": len(df),
                "successful_transactions": len(successful_df),
                "revenue": float(successful_df['commission'].sum()),
                "volume": float(successful_df['amount'].sum()),
                "success_rate": round(len(successful_df) / len(df) * 100, 2) if len(df) > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error in _get_education_analytics: {str(e)}")
            return {"error": str(e)}


class SystemHealthService:
    """Service for monitoring system health and performance"""
    
    @staticmethod
    def get_system_health() -> Dict[str, Any]:
        """Get overall system health metrics"""
        try:
            # Recent error rates
            recent_errors = SystemHealthService._get_recent_error_rates()
            
            # Database performance indicators
            db_health = SystemHealthService._check_database_health()
            
            # Service availability
            service_health = SystemHealthService._check_service_health()
            
            return {
                "error_rates": recent_errors,
                "database_health": db_health,
                "service_health": service_health,
                "overall_status": "healthy" if all([
                    recent_errors.get("error_rate", 100) < 10,
                    db_health.get("status") == "healthy",
                    service_health.get("status") == "healthy"
                ]) else "degraded",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in get_system_health: {str(e)}")
            return {"error": str(e), "overall_status": "error"}
    
    @staticmethod
    def _get_recent_error_rates() -> Dict[str, Any]:
        """Calculate recent error rates"""
        try:
            # Last 24 hours
            end_date = datetime.now()
            start_date = end_date - timedelta(hours=24)
            
            recent_transactions = supabase.table('history').select('status').gte(
                'created_at', start_date.isoformat()
            ).execute()
            
            if not recent_transactions.data:
                return {"error_rate": 0, "total_transactions": 0}
            
            total = len(recent_transactions.data)
            failed = len([tx for tx in recent_transactions.data if tx.get('status') == 'failed'])
            error_rate = (failed / total * 100) if total > 0 else 0
            
            return {
                "error_rate": round(error_rate, 2),
                "total_transactions": total,
                "failed_transactions": failed,
                "period_hours": 24
            }
            
        except Exception as e:
            logger.error(f"Error in _get_recent_error_rates: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    def _check_database_health() -> Dict[str, Any]:
        """Check database connectivity and performance"""
        try:
            # Simple connectivity test
            start_time = datetime.now()
            test_response = supabase.table('profile').select('id').limit(1).execute()
            end_time = datetime.now()
            
            response_time = (end_time - start_time).total_seconds() * 1000  # in milliseconds
            
            return {
                "status": "healthy" if test_response.data is not None else "unhealthy",
                "response_time_ms": round(response_time, 2),
                "connectivity": "good" if response_time < 1000 else "slow"
            }
            
        except Exception as e:
            logger.error(f"Error in _check_database_health: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    @staticmethod
    def _check_service_health() -> Dict[str, Any]:
        """Check health of various services"""
        try:
            # Check recent successful transactions for each service type
            end_date = datetime.now()
            start_date = end_date - timedelta(hours=1)
            
            service_types = ['data_topup', 'airtime_topup', 'electricity_topup', 'tv_topup', 'education_topup']
            service_health = {}
            
            for service_type in service_types:
                recent_success = supabase.table('history').select('id').eq(
                    'type', service_type
                ).eq('status', 'success').gte(
                    'created_at', start_date.isoformat()
                ).limit(1).execute()
                
                service_health[service_type] = "healthy" if recent_success.data else "inactive"
            
            overall_healthy = sum(1 for status in service_health.values() if status == "healthy")
            total_services = len(service_types)
            
            return {
                "status": "healthy" if overall_healthy >= total_services * 0.8 else "degraded",
                "service_breakdown": service_health,
                "healthy_services": overall_healthy,
                "total_services": total_services
            }
            
        except Exception as e:
            logger.error(f"Error in _check_service_health: {str(e)}")
            return {"status": "error", "error": str(e)}
