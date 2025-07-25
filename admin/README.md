# iSubscribe Admin API Documentation

## Overview

The iSubscribe Admin API provides comprehensive analytics, monitoring, and management capabilities for the iSubscribe telecom platform. This robust admin system offers detailed insights into user behavior, financial performance, transaction monitoring, and system health.

## Features

### 📊 **Analytics & Insights**
- **User Analytics**: Growth metrics, engagement analysis, demographics
- **Financial Analytics**: Revenue tracking, commission analysis, wallet insights
- **Transaction Analytics**: Success rates, provider performance, suspicious activity detection
- **Service Analytics**: Performance metrics for data, airtime, bills, and education services

### 🔍 **Monitoring & Health**
- **System Health**: Real-time monitoring of database connectivity and service availability
- **Error Tracking**: Comprehensive error rate analysis and alerting
- **Performance Metrics**: Response time monitoring and bottleneck identification

### 👥 **User Management**
- **User Search**: Advanced filtering and search capabilities
- **Account Actions**: Suspend, activate, balance adjustments, role management
- **Transaction History**: Detailed view of user activities
- **Security Monitoring**: Account status and security profile tracking

### 📈 **Reporting & Export**
- **Revenue Reports**: Daily, weekly, monthly revenue breakdowns
- **Data Export**: CSV and JSON export for users, transactions, and revenue data
- **Custom Reports**: Flexible reporting with date ranges and filters

## Authentication

All admin endpoints require authentication using the `AdminSupabaseAuthentication` class. Users must have either `admin` or `super_admin` role in their profile.

### Headers
```
Authorization: Bearer <supabase-jwt-token>
Content-Type: application/json
```

## Permission Levels

- **IsAdminUser**: Basic admin access (admin or super_admin role)
- **IsSuperAdminUser**: Super admin only access
- **CanViewAnalytics**: Permission to view analytics data
- **CanModifyUsers**: Permission to modify user accounts (super_admin only)
- **CanViewFinancials**: Permission to view financial data

## API Endpoints

### Dashboard
```
GET /api/v1/admin/dashboard/
```
Main dashboard overview with key metrics and recent activities.

**Query Parameters:**
- `days` (int): Number of days to analyze (default: 30)

**Response:**
```json
{
  "success": true,
  "message": "Dashboard data retrieved successfully",
  "data": {
    "overview": {
      "total_users": 1500,
      "total_revenue": 75000.00,
      "total_transactions": 3200,
      "success_rate": 95.8,
      "system_status": "healthy"
    },
    "user_metrics": {
      "total_users": 1500,
      "new_users": 45,
      "active_users": 320,
      "growth_rate": 3.1
    },
    "financial_metrics": {
      "total_revenue": 75000.00,
      "total_volume": 1250000.00,
      "success_rate": 95.8,
      "daily_trends": [...]
    },
    "system_health": {
      "overall_status": "healthy",
      "database_health": {"status": "healthy"},
      "service_health": {"status": "healthy"}
    },
    "recent_activities": [...]
  }
}
```

### User Analytics
```
GET /api/v1/admin/analytics/users/
```
Detailed user analytics including growth and engagement metrics.

**Query Parameters:**
- `days` (int): Number of days to analyze (default: 30)

### Financial Analytics
```
GET /api/v1/admin/analytics/financial/
```
Comprehensive financial analytics and revenue insights.

**Query Parameters:**
- `start_date` (string): Start date in ISO format
- `end_date` (string): End date in ISO format
- `days` (int): Number of days if dates not provided (default: 30)

### Transaction Analytics
```
GET /api/v1/admin/analytics/transactions/
```
Transaction monitoring and analysis including suspicious activities.

**Query Parameters:**
- `days` (int): Number of days to analyze (default: 30)

### Service Analytics
```
GET /api/v1/admin/analytics/services/
```
Performance analytics for all services (data, airtime, bills, education).

**Query Parameters:**
- `days` (int): Number of days to analyze (default: 30)

### System Health
```
GET /api/v1/admin/system/health/
```
System health monitoring including database connectivity and service availability.

### User Management

#### List Users
```
GET /api/v1/admin/users/
```
Paginated list of users with advanced filtering.

**Query Parameters:**
- `limit` (int): Number of users to return (default: 50)
- `offset` (int): Number of users to skip (default: 0)
- `search` (string): Search term for email, name, or phone
- `role` (string): Filter by user role
- `created_after` (string): Filter users created after date
- `created_before` (string): Filter users created before date

#### Get User Details
```
GET /api/v1/admin/users/{id}/
```
Detailed information about a specific user.

#### User Actions
```
POST /api/v1/admin/users/{id}/actions/
```
Perform administrative actions on user accounts.

**Request Body:**
```json
{
  "action": "suspend|activate|adjust_balance|reset_pin|set_role",
  "amount": 100.0,  // For adjust_balance
  "role": "admin",   // For set_role
  "reason": "Admin action reason"
}
```

### Transaction Management
```
GET /api/v1/admin/transactions/
```
Advanced transaction search with comprehensive filtering.

**Query Parameters:**
- `limit`, `offset`: Pagination
- `search`: Search in description, email, transaction_id
- `status`: Filter by status (successful, failed, pending)
- `type`: Filter by type (data_bundle, airtime, electricity, etc.)
- `provider`: Filter by provider
- `amount_min`, `amount_max`: Amount range filter
- `date_from`, `date_to`: Date range filter
- `user_id`: Filter by specific user

### Reports

#### Revenue Reports
```
GET /api/v1/admin/reports/revenue/
```
Generate comprehensive revenue reports.

**Query Parameters:**
- `period`: daily, weekly, monthly (default: daily)
- `start_date`, `end_date`: Date range
- `format`: json, csv (default: json)

#### Data Export
```
GET /api/v1/admin/reports/export/
```
Export data in various formats.

**Query Parameters:**
- `type`: users, transactions, revenue
- `format`: csv, json
- `start_date`, `end_date`: Date range for filtering

## Response Format

All endpoints follow the ResponseMixin pattern:

```json
{
  "success": true,
  "message": "Description of the operation",
  "data": { ... },
  "error": null,
  "count": 100,    // For paginated responses
  "next": 50,      // Next offset for pagination
  "previous": 0    // Previous offset for pagination
}
```

## Error Handling

Error responses follow the same format:

```json
{
  "success": false,
  "message": "Error description",
  "data": null,
  "error": {
    "detail": "Specific error details"
  }
}
```

## Security Features

### Authentication
- JWT token validation through Supabase
- Role-based access control
- Admin-only endpoints protection

### Authorization
- Granular permissions for different operations
- Super admin restrictions for sensitive actions
- Audit logging for all admin actions

### Data Protection
- Sensitive data masking
- Rate limiting on endpoints
- Request validation and sanitization

## Analytics Insights

### User Metrics
- **Growth Rate**: Percentage increase in user registrations
- **Activity Rate**: Percentage of active users
- **Retention Analysis**: User engagement over time
- **Geographic Distribution**: Users by state/region

### Financial Metrics
- **Revenue Trends**: Daily, weekly, monthly revenue patterns
- **Commission Analysis**: Earnings by service type and provider
- **Wallet Analytics**: Balance distribution and usage patterns
- **Growth Metrics**: Revenue growth comparisons

### Transaction Metrics
- **Success Rates**: Transaction success/failure analysis
- **Provider Performance**: Performance comparison across providers
- **Suspicious Activity Detection**: Fraud and abuse monitoring
- **Usage Patterns**: Peak hours and service preferences

### Service Metrics
- **Service Performance**: Success rates by service type
- **Revenue Contribution**: Revenue share by service
- **User Preferences**: Most popular services and plans
- **Provider Comparison**: Performance metrics across providers

## Usage Examples

### Get Dashboard Overview
```bash
curl -X GET "https://api.isubscribe.com/api/v1/admin/dashboard/" \
  -H "Authorization: Bearer <admin-token>"
```

### Search Users
```bash
curl -X GET "https://api.isubscribe.com/api/v1/admin/users/?search=john&limit=20" \
  -H "Authorization: Bearer <admin-token>"
```

### Adjust User Balance
```bash
curl -X POST "https://api.isubscribe.com/api/v1/admin/users/123/actions/" \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "adjust_balance",
    "amount": 500.0,
    "reason": "Bonus credit"
  }'
```

### Export Revenue Report as CSV
```bash
curl -X GET "https://api.isubscribe.com/api/v1/admin/reports/revenue/?format=csv&period=monthly" \
  -H "Authorization: Bearer <admin-token>" \
  --output revenue_report.csv
```

## Performance Considerations

- **Pagination**: All list endpoints support pagination to handle large datasets
- **Caching**: Analytics data is cached for improved performance
- **Async Processing**: Long-running reports are processed asynchronously
- **Rate Limiting**: API calls are rate-limited to prevent abuse

## Best Practices

1. **Regular Monitoring**: Check system health and error rates regularly
2. **Data Backup**: Export critical data periodically
3. **Access Control**: Use appropriate permission levels for different admin roles
4. **Audit Trails**: Monitor admin actions through logging
5. **Performance Optimization**: Use pagination and filtering for large datasets

## Support

For technical support or questions about the Admin API:
- Email: tech-support@isubscribe.com
- Documentation: https://docs.isubscribe.com/admin-api
- Status Page: https://status.isubscribe.com
