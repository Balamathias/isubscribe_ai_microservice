"""
Advanced Email Service for Admin Operations

This module provides sophisticated email functionality for admin operations,
including beautiful templates, bulk messaging, and professional notifications.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from services.supabase import superbase as supabase

logger = logging.getLogger(__name__)


class EmailTemplateService:
    """Service for managing and rendering email templates"""
    
    # Template categories with their respective templates
    TEMPLATES = {
        'notifications': {
            'general_announcement': {
                'name': 'General Announcement',
                'description': 'General platform announcements and updates',
                'subject_template': '{announcement_title} - isubscribe',
                'requires': ['announcement_title', 'announcement_content']
            },
            'maintenance_notice': {
                'name': 'Maintenance Notice',
                'description': 'System maintenance notifications',
                'subject_template': 'Scheduled Maintenance - {maintenance_date}',
                'requires': ['maintenance_date', 'maintenance_duration', 'affected_services']
            },
            'service_update': {
                'name': 'Service Update',
                'description': 'New feature announcements and service updates',
                'subject_template': 'New Feature: {feature_name}',
                'requires': ['feature_name', 'feature_description', 'release_date']
            }
        },
        'transactional': {
            'transaction_reversed': {
                'name': 'Transaction Reversed',
                'description': 'Notification for reversed transactions',
                'subject_template': 'Transaction Reversed - ₦{amount}',
                'requires': ['transaction_id', 'amount', 'reason', 'reversal_date']
            },
            'account_adjustment': {
                'name': 'Account Balance Adjustment',
                'description': 'Balance adjustment notifications',
                'subject_template': 'Account Balance Adjustment - ₦{adjustment_amount}',
                'requires': ['adjustment_amount', 'adjustment_reason', 'new_balance']
            },
            'refund_processed': {
                'name': 'Refund Processed',
                'description': 'Refund confirmation emails',
                'subject_template': 'Refund Processed - ₦{refund_amount}',
                'requires': ['refund_amount', 'transaction_id', 'processing_date']
            }
        },
        'promotional': {
            'welcome_bonus': {
                'name': 'Welcome Bonus',
                'description': 'Welcome bonus notifications for new users',
                'subject_template': 'Welcome to isubscribe! Your ₦{bonus_amount} bonus awaits',
                'requires': ['bonus_amount', 'bonus_expires']
            },
            'cashback_earned': {
                'name': 'Cashback Earned',
                'description': 'Cashback reward notifications',
                'subject_template': 'You earned ₦{cashback_amount} cashback!',
                'requires': ['cashback_amount', 'transaction_details']
            },
            'special_offer': {
                'name': 'Special Offer',
                'description': 'Special promotional offers',
                'subject_template': '{offer_title} - Limited Time Offer',
                'requires': ['offer_title', 'offer_description', 'offer_expires']
            }
        },
        'administrative': {
            'account_suspended': {
                'name': 'Account Suspended',
                'description': 'Account suspension notifications',
                'subject_template': 'Important: Your isubscribe Account Status',
                'requires': ['suspension_reason', 'suspension_date', 'appeal_process']
            },
            'account_reactivated': {
                'name': 'Account Reactivated',
                'description': 'Account reactivation confirmations',
                'subject_template': 'Welcome Back! Your Account is Now Active',
                'requires': ['reactivation_date', 'welcome_message']
            },
            'security_alert': {
                'name': 'Security Alert',
                'description': 'Security-related notifications',
                'subject_template': 'Security Alert - isubscribe Account',
                'requires': ['alert_type', 'alert_description', 'recommended_actions']
            }
        }
    }

    @classmethod
    def get_template_categories(cls) -> Dict[str, Any]:
        """Get all available template categories"""
        return {
            category: {
                'name': category.replace('_', ' ').title(),
                'templates': list(templates.keys()),
                'template_details': templates
            }
            for category, templates in cls.TEMPLATES.items()
        }

    @classmethod
    def get_template_info(cls, category: str, template_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific template"""
        if category in cls.TEMPLATES and template_id in cls.TEMPLATES[category]:
            return cls.TEMPLATES[category][template_id]
        return None

    @classmethod
    def render_email_template(cls, template_category: str, template_id: str, 
                            context: Dict[str, Any], recipient_name: str = None) -> Dict[str, str]:
        """Render email template with context"""
        try:
            template_info = cls.get_template_info(template_category, template_id)
            if not template_info:
                raise ValueError(f"Template {template_category}/{template_id} not found")

            # Validate required fields
            missing_fields = [field for field in template_info['requires'] if field not in context]
            if missing_fields:
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

            # Add default context
            context.update({
                'recipient_name': recipient_name or 'Valued Customer',
                'current_year': datetime.now().year,
                'support_email': 'support@isubscribe.ng',
                'website_url': 'https://isubscribe.ng',
                'company_name': 'isubscribe',
                'primary_color': '#7C3AED',  # Violet
                'secondary_color': '#A855F7',
                'accent_color': '#C084FC'
            })

            # Generate subject
            subject = template_info['subject_template'].format(**context)

            # Generate HTML content
            html_content = cls._generate_html_template(template_category, template_id, context)
            
            # Generate plain text content
            plain_content = cls._generate_plain_template(template_category, template_id, context)

            return {
                'subject': subject,
                'html_content': html_content,
                'plain_content': plain_content
            }

        except Exception as e:
            logger.error(f"Error rendering email template: {str(e)}")
            raise

    @classmethod
    def _generate_html_template(cls, category: str, template_id: str, context: Dict[str, Any]) -> str:
        """Generate beautiful HTML email template"""
        
        # Base email template structure
        base_template = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{context.get('subject', 'isubscribe Notification')}</title>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
                
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #334155;
                    background-color: #f8fafc;
                    margin: 0;
                    padding: 0;
                }}
                
                .email-container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: #ffffff;
                    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
                }}
                
                .header {{
                    background: linear-gradient(135deg, {context['primary_color']} 0%, {context['secondary_color']} 100%);
                    padding: 40px 30px;
                    text-align: center;
                    color: white;
                }}
                
                .logo {{
                    font-size: 32px;
                    font-weight: 700;
                    margin-bottom: 10px;
                    letter-spacing: -0.5px;
                }}
                
                .header-subtitle {{
                    font-size: 16px;
                    opacity: 0.9;
                    font-weight: 300;
                }}
                
                .content {{
                    padding: 40px 30px;
                }}
                
                .greeting {{
                    font-size: 20px;
                    font-weight: 600;
                    color: #1e293b;
                    margin-bottom: 20px;
                }}
                
                .main-content {{
                    font-size: 16px;
                    line-height: 1.7;
                    margin-bottom: 30px;
                }}
                
                .highlight-box {{
                    background: linear-gradient(135deg, {context['primary_color']}10, {context['accent_color']}10);
                    border-left: 4px solid {context['primary_color']};
                    padding: 20px;
                    margin: 25px 0;
                    border-radius: 0 8px 8px 0;
                }}
                
                .amount {{
                    font-size: 32px;
                    font-weight: 700;
                    color: {context['primary_color']};
                    text-align: center;
                    margin: 20px 0;
                }}
                
                .button {{
                    display: inline-block;
                    background: linear-gradient(135deg, {context['primary_color']} 0%, {context['secondary_color']} 100%);
                    color: white;
                    text-decoration: none;
                    padding: 15px 30px;
                    border-radius: 8px;
                    font-weight: 600;
                    font-size: 16px;
                    margin: 20px 0;
                    transition: all 0.3s ease;
                    box-shadow: 0 4px 15px rgba(124, 58, 237, 0.3);
                }}
                
                .button:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(124, 58, 237, 0.4);
                }}
                
                .info-grid {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 20px;
                    margin: 25px 0;
                }}
                
                .info-item {{
                    background: #f8fafc;
                    padding: 15px;
                    border-radius: 8px;
                    border: 1px solid #e2e8f0;
                }}
                
                .info-label {{
                    font-size: 12px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    color: #64748b;
                    margin-bottom: 5px;
                    font-weight: 500;
                }}
                
                .info-value {{
                    font-size: 16px;
                    font-weight: 600;
                    color: #1e293b;
                }}
                
                .footer {{
                    background-color: #f8fafc;
                    padding: 30px;
                    text-align: center;
                    border-top: 1px solid #e2e8f0;
                }}
                
                .footer-content {{
                    font-size: 14px;
                    color: #64748b;
                    margin-bottom: 15px;
                }}
                
                .social-links {{
                    margin: 20px 0;
                }}
                
                .social-link {{
                    display: inline-block;
                    margin: 0 10px;
                    color: {context['primary_color']};
                    text-decoration: none;
                }}
                
                .warning {{
                    background: #fef3c7;
                    border: 1px solid #f59e0b;
                    color: #92400e;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 20px 0;
                }}
                
                .success {{
                    background: #d1fae5;
                    border: 1px solid #10b981;
                    color: #065f46;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 20px 0;
                }}
                
                @media only screen and (max-width: 600px) {{
                    .email-container {{
                        margin: 0;
                        width: 100% !important;
                    }}
                    
                    .header, .content, .footer {{
                        padding: 25px 20px;
                    }}
                    
                    .info-grid {{
                        grid-template-columns: 1fr;
                    }}
                    
                    .amount {{
                        font-size: 28px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="header">
                    <div class="logo">isubscribe</div>
                    <div class="header-subtitle">Your Digital Services Platform</div>
                </div>
                
                <div class="content">
                    <div class="greeting">Hello {context['recipient_name']},</div>
                    
                    <div class="main-content">
                        {cls._get_template_content(category, template_id, context)}
                    </div>
                </div>
                
                <div class="footer">
                    <div class="footer-content">
                        This email was sent from isubscribe. If you have any questions, 
                        please contact our support team at <strong>{context['support_email']}</strong>
                    </div>
                    
                    <div class="social-links">
                        <a href="{context['website_url']}" class="social-link">Visit Website</a>
                        <a href="mailto:{context['support_email']}" class="social-link">Contact Support</a>
                    </div>
                    
                    <div class="footer-content">
                        © {context['current_year']} {context['company_name']}. All rights reserved.
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return base_template

    @classmethod
    def _get_template_content(cls, category: str, template_id: str, context: Dict[str, Any]) -> str:
        """Get specific template content based on category and template ID"""
        
        if category == 'notifications':
            if template_id == 'general_announcement':
                return f"""
                <div class="highlight-box">
                    <h2 style="color: {context['primary_color']}; margin-bottom: 15px;">{context['announcement_title']}</h2>
                    <p>{context['announcement_content']}</p>
                </div>
                <p>We wanted to make sure you're kept informed about this important update to our platform.</p>
                <p>If you have any questions, please don't hesitate to reach out to our support team.</p>
                """
            elif template_id == 'maintenance_notice':
                return f"""
                <div class="warning">
                    <strong>Scheduled Maintenance Notice</strong>
                </div>
                <p>We will be performing scheduled maintenance on <strong>{context['maintenance_date']}</strong>.</p>
                <div class="info-grid">
                    <div class="info-item">
                        <div class="info-label">Duration</div>
                        <div class="info-value">{context['maintenance_duration']}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Affected Services</div>
                        <div class="info-value">{context['affected_services']}</div>
                    </div>
                </div>
                <p>During this time, you may experience brief service interruptions. We appreciate your patience as we work to improve our platform.</p>
                """
            elif template_id == 'service_update':
                return f"""
                <div class="success">
                    <strong>New Feature Available!</strong>
                </div>
                <h3 style="color: {context['primary_color']};">{context['feature_name']}</h3>
                <p>{context['feature_description']}</p>
                <div class="highlight-box">
                    <p><strong>Available from:</strong> {context['release_date']}</p>
                </div>
                <a href="{context['website_url']}" class="button">Explore New Feature</a>
                """
                
        elif category == 'transactional':
            if template_id == 'transaction_reversed':
                return f"""
                <div class="highlight-box">
                    <p><strong>Transaction Reversal Notification</strong></p>
                </div>
                <p>We have successfully reversed your transaction as requested.</p>
                <div class="amount">₦{context['amount']}</div>
                <div class="info-grid">
                    <div class="info-item">
                        <div class="info-label">Transaction ID</div>
                        <div class="info-value">{context['transaction_id']}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Reversal Date</div>
                        <div class="info-value">{context['reversal_date']}</div>
                    </div>
                </div>
                <p><strong>Reason:</strong> {context['reason']}</p>
                <p>The amount has been credited back to your wallet and should reflect in your balance shortly.</p>
                """
            elif template_id == 'account_adjustment':
                return f"""
                <div class="highlight-box">
                    <p><strong>Account Balance Adjustment</strong></p>
                </div>
                <p>Your account balance has been adjusted by our team.</p>
                <div class="amount">₦{context['adjustment_amount']}</div>
                <div class="info-grid">
                    <div class="info-item">
                        <div class="info-label">Adjustment Reason</div>
                        <div class="info-value">{context['adjustment_reason']}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">New Balance</div>
                        <div class="info-value">₦{context['new_balance']}</div>
                    </div>
                </div>
                <p>If you have any questions about this adjustment, please contact our support team.</p>
                """
            elif template_id == 'refund_processed':
                return f"""
                <div class="success">
                    <strong>Refund Processed Successfully</strong>
                </div>
                <p>Good news! Your refund has been processed and credited to your wallet.</p>
                <div class="amount">₦{context['refund_amount']}</div>
                <div class="info-grid">
                    <div class="info-item">
                        <div class="info-label">Original Transaction</div>
                        <div class="info-value">{context['transaction_id']}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Processing Date</div>
                        <div class="info-value">{context['processing_date']}</div>
                    </div>
                </div>
                <p>The refunded amount is now available in your wallet for immediate use.</p>
                """
                
        elif category == 'promotional':
            if template_id == 'welcome_bonus':
                return f"""
                <div class="success">
                    <strong>Welcome to isubscribe! 🎉</strong>
                </div>
                <p>Thank you for joining isubscribe! We're excited to have you on board.</p>
                <div class="highlight-box">
                    <p style="text-align: center; margin: 0;">Your Welcome Bonus</p>
                    <div class="amount">₦{context['bonus_amount']}</div>
                    <p style="text-align: center; margin: 0;"><small>Expires: {context['bonus_expires']}</small></p>
                </div>
                <p>This bonus has been automatically added to your wallet and can be used for any of our services including data bundles, airtime, bills payment, and more!</p>
                <a href="{context['website_url']}" class="button">Start Using Your Bonus</a>
                """
            elif template_id == 'cashback_earned':
                return f"""
                <div class="success">
                    <strong>Congratulations! You've Earned Cashback! 💰</strong>
                </div>
                <p>Great news! You've earned cashback on your recent transaction.</p>
                <div class="amount">₦{context['cashback_amount']}</div>
                <div class="highlight-box">
                    <p><strong>Transaction Details:</strong></p>
                    <p>{context['transaction_details']}</p>
                </div>
                <p>Your cashback has been automatically added to your wallet balance and is ready to use!</p>
                <a href="{context['website_url']}" class="button">View Wallet Balance</a>
                """
            elif template_id == 'special_offer':
                return f"""
                <div class="highlight-box">
                    <h2 style="color: {context['primary_color']}; margin-bottom: 15px;">🎁 {context['offer_title']}</h2>
                    <p>{context['offer_description']}</p>
                </div>
                <div class="warning">
                    <strong>⏰ Limited Time Only!</strong><br>
                    This offer expires on {context['offer_expires']}
                </div>
                <p>Don't miss out on this exclusive opportunity to save more on your favorite services!</p>
                <a href="{context['website_url']}" class="button">Claim This Offer</a>
                """
                
        elif category == 'administrative':
            if template_id == 'account_suspended':
                return f"""
                <div class="warning">
                    <strong>⚠️ Important Account Notice</strong>
                </div>
                <p>We regret to inform you that your isubscribe account has been temporarily suspended.</p>
                <div class="info-grid">
                    <div class="info-item">
                        <div class="info-label">Suspension Date</div>
                        <div class="info-value">{context['suspension_date']}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Reason</div>
                        <div class="info-value">{context['suspension_reason']}</div>
                    </div>
                </div>
                <div class="highlight-box">
                    <p><strong>Appeal Process:</strong></p>
                    <p>{context['appeal_process']}</p>
                </div>
                <p>If you believe this suspension was made in error, please contact our support team immediately.</p>
                """
            elif template_id == 'account_reactivated':
                return f"""
                <div class="success">
                    <strong>🎉 Welcome Back!</strong>
                </div>
                <p>Great news! Your isubscribe account has been reactivated and is now fully functional.</p>
                <div class="highlight-box">
                    <p><strong>Reactivation Date:</strong> {context['reactivation_date']}</p>
                </div>
                <p>{context['welcome_message']}</p>
                <p>You can now access all services including data bundles, airtime top-up, bill payments, and educational services.</p>
                <a href="{context['website_url']}" class="button">Access Your Account</a>
                """
            elif template_id == 'security_alert':
                return f"""
                <div class="warning">
                    <strong>🔒 Security Alert</strong>
                </div>
                <p>We detected {context['alert_type']} on your account and wanted to notify you immediately.</p>
                <div class="highlight-box">
                    <p><strong>Alert Details:</strong></p>
                    <p>{context['alert_description']}</p>
                </div>
                <div class="info-grid">
                    <div class="info-item">
                        <div class="info-label">Recommended Actions</div>
                        <div class="info-value">{context['recommended_actions']}</div>
                    </div>
                </div>
                <p>If this activity was not authorized by you, please contact our support team immediately.</p>
                <a href="mailto:{context['support_email']}" class="button">Contact Support</a>
                """
        
        return "<p>Content not available for this template.</p>"

    @classmethod
    def _generate_plain_template(cls, category: str, template_id: str, context: Dict[str, Any]) -> str:
        """Generate plain text version of email template"""
        
        plain_header = f"""
Hello {context['recipient_name']},

"""
        
        plain_footer = f"""

Best regards,
The isubscribe Team

Support: {context['support_email']}
Website: {context['website_url']}

© {context['current_year']} {context['company_name']}. All rights reserved.
        """
        
        # Generate content based on template
        if category == 'notifications':
            if template_id == 'general_announcement':
                content = f"""
{context['announcement_title']}

{context['announcement_content']}

We wanted to make sure you're kept informed about this important update to our platform.
"""
            elif template_id == 'maintenance_notice':
                content = f"""
SCHEDULED MAINTENANCE NOTICE

We will be performing scheduled maintenance on {context['maintenance_date']}.

Duration: {context['maintenance_duration']}
Affected Services: {context['affected_services']}

During this time, you may experience brief service interruptions.
"""
            elif template_id == 'service_update':
                content = f"""
NEW FEATURE AVAILABLE!

{context['feature_name']}

{context['feature_description']}

Available from: {context['release_date']}
"""
        elif category == 'transactional':
            if template_id == 'transaction_reversed':
                content = f"""
TRANSACTION REVERSAL NOTIFICATION

We have successfully reversed your transaction as requested.

Amount: ₦{context['amount']}
Transaction ID: {context['transaction_id']}
Reversal Date: {context['reversal_date']}
Reason: {context['reason']}

The amount has been credited back to your wallet.
"""
            elif template_id == 'account_adjustment':
                content = f"""
ACCOUNT BALANCE ADJUSTMENT

Your account balance has been adjusted by our team.

Adjustment Amount: ₦{context['adjustment_amount']}
Reason: {context['adjustment_reason']}
New Balance: ₦{context['new_balance']}
"""
            elif template_id == 'refund_processed':
                content = f"""
REFUND PROCESSED SUCCESSFULLY

Your refund has been processed and credited to your wallet.

Refund Amount: ₦{context['refund_amount']}
Original Transaction: {context['transaction_id']}
Processing Date: {context['processing_date']}
"""
        else:
            content = "Email content not available in plain text format."
            
        return plain_header + content + plain_footer


class AdminEmailService:
    """Service for admin email operations"""
    
    @staticmethod
    def send_email(recipients: Union[str, List[str]], template_category: str, 
                   template_id: str, context: Dict[str, Any], 
                   sender_email: str = None, recipient_names: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Send email using specified template
        
        Args:
            recipients: Email address(es) to send to
            template_category: Category of template
            template_id: Specific template ID
            context: Template context data
            sender_email: Sender email (optional)
            recipient_names: Mapping of email to recipient name (optional)
            
        Returns:
            Dict with success status and details
        """
        try:
            if isinstance(recipients, str):
                recipients = [recipients]
            
            sender_email = sender_email or settings.DEFAULT_FROM_EMAIL
            recipient_names = recipient_names or {}
            
            sent_count = 0
            failed_recipients = []
            
            for recipient in recipients:
                try:
                    recipient_name = recipient_names.get(recipient, 'Valued Customer')
                    
                    # Render template
                    email_content = EmailTemplateService.render_email_template(
                        template_category, template_id, context, recipient_name
                    )
                    
                    # Create email message
                    email = EmailMultiAlternatives(
                        subject=email_content['subject'],
                        body=email_content['plain_content'],
                        from_email=sender_email,
                        to=[recipient]
                    )
                    
                    # Attach HTML version
                    email.attach_alternative(email_content['html_content'], "text/html")
                    
                    # Send email
                    email.send()
                    sent_count += 1
                    
                    # Log email sent
                    logger.info(f"Email sent successfully to {recipient} using template {template_category}/{template_id}")
                    
                except Exception as e:
                    logger.error(f"Failed to send email to {recipient}: {str(e)}")
                    failed_recipients.append({"email": recipient, "error": str(e)})
            
            return {
                "success": True,
                "sent_count": sent_count,
                "total_recipients": len(recipients),
                "failed_recipients": failed_recipients,
                "message": f"Successfully sent {sent_count} out of {len(recipients)} emails"
            }
            
        except Exception as e:
            logger.error(f"Error in admin email service: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to send emails"
            }

    @staticmethod
    def send_bulk_announcement(user_filters: Dict[str, Any], template_category: str,
                             template_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send bulk announcement emails to filtered users
        
        Args:
            user_filters: Filters to select users
            template_category: Email template category
            template_id: Email template ID
            context: Template context
            
        Returns:
            Dict with success status and details
        """
        try:
            # Build user query based on filters
            query = supabase.table('profile').select('email, full_name')
            
            # Apply filters
            if user_filters.get('role'):
                query = query.eq('role', user_filters['role'])
            
            if user_filters.get('created_after'):
                query = query.gte('created_at', user_filters['created_after'])
                
            if user_filters.get('created_before'):
                query = query.lte('created_at', user_filters['created_before'])
                
            if user_filters.get('status'):
                query = query.eq('status', user_filters['status'])
            
            # Get users
            users_response = query.execute()
            users = users_response.data if users_response.data else []
            
            if not users:
                return {
                    "success": False,
                    "message": "No users found matching the specified filters"
                }
            
            # Prepare recipient data
            recipients = [user['email'] for user in users if user.get('email')]
            recipient_names = {user['email']: user.get('full_name', 'Valued Customer') 
                             for user in users if user.get('email')}
            
            # Send emails
            result = AdminEmailService.send_email(
                recipients=recipients,
                template_category=template_category,
                template_id=template_id,
                context=context,
                recipient_names=recipient_names
            )
            
            # Log bulk email operation
            logger.info(f"Bulk email sent to {len(recipients)} users using template {template_category}/{template_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in bulk announcement: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to send bulk announcement"
            }
