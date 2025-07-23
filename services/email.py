import os
import logging
from typing import Dict, Any, Optional
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

logger = logging.getLogger(__name__)

def send_otp_email(email: str, otp: str, full_name: str) -> Dict[str, Any]:
    """
    Send OTP email to user for PIN reset
    
    Args:
        email: User's email address
        otp: The OTP code
        full_name: User's full name
        
    Returns:
        Dict with success status and optional error message
    """
    try:
        subject = "Your PIN Reset Code - iSubscribe"
        
        html_message = f"""//js
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #f8f9fa; padding: 30px; border-radius: 10px;">
                <h2 style="color: #333; text-align: center; margin-bottom: 30px;">PIN Reset Request</h2>
                
                <p style="color: #666; font-size: 16px;">Hello {full_name},</p>
                
                <p style="color: #666; font-size: 16px;">
                    You have requested to reset your transaction PIN. Please use the code below to complete the process:
                </p>
                
                <div style="background-color: #fff; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0;">
                    <h1 style="color: #007bff; font-size: 32px; letter-spacing: 5px; margin: 0;">{otp}</h1>
                </div>
                
                <p style="color: #666; font-size: 14px;">
                    This code will expire in 10 minutes. If you didn't request this PIN reset, please ignore this email.
                </p>
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                    <p style="color: #999; font-size: 12px; text-align: center;">
                        This is an automated message from isubscribe. Please do not reply to this email.
                    </p>
                </div>
            </div>
        </body>
        </html>
        ;//
        """.replace("//js", "").replace(";//", "")
        
        plain_message = f"""
        Hello {full_name},
        
        You have requested to reset your transaction PIN. Please use the code below to complete the process:
        
        {otp}
        
        This code will expire in 10 minutes. If you didn't request this PIN reset, please ignore this email.
        
        Best regards,
        isubscribe Team
        """
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"OTP email sent successfully to {email}")
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Error sending OTP email to {email}: {str(e)}")
        return {
            "error": {
                "message": f"Failed to send email: {str(e)}"
            }
        }