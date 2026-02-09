"""Notification service for email, SMS, and in-app notifications."""

from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from twilio.rest import Client as TwilioClient
from twilio.base.exceptions import TwilioRestException

from app.core.config import settings
from app.core.exceptions import IntegrationError, ValidationError, DatabaseError


# Note: Notification model should be created separately
# For now, notifications will be logged and sent via email/SMS only


async def send_email(
    to: str,
    subject: str,
    body: str,
    from_email: Optional[str] = None,
    html_body: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send email using SendGrid.
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Plain text email body
        from_email: Sender email (uses default if not provided)
        html_body: Optional HTML body (will use plain text if not provided)
        
    Returns:
        Dictionary with send status and message ID
        
    Raises:
        IntegrationError: If SendGrid API call fails
        ValidationError: If email parameters are invalid
    """
    if not to or "@" not in to:
        raise ValidationError("Invalid recipient email address")
    
    if not subject or not body:
        raise ValidationError("Email subject and body are required")
    
    if not settings.SENDGRID_API_KEY:
        # Log email instead of sending in development
        print(f"[EMAIL] To: {to}, Subject: {subject}, Body: {body[:100]}...")
        return {
            "success": True,
            "message_id": "dev-mode-no-send",
            "status": "logged"
        }
    
    try:
        # Create SendGrid client
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        
        # Prepare email
        from_addr = from_email or settings.FROM_EMAIL
        message = Mail(
            from_email=Email(from_addr),
            to_emails=To(to),
            subject=subject,
            plain_text_content=Content("text/plain", body)
        )
        
        # Add HTML content if provided
        if html_body:
            message.add_content(Content("text/html", html_body))
        
        # Send email
        response = sg.send(message)
        
        return {
            "success": True,
            "message_id": response.headers.get("X-Message-Id", "unknown"),
            "status_code": response.status_code,
            "to": to,
            "subject": subject
        }
        
    except Exception as e:
        raise IntegrationError(
            f"Failed to send email: {str(e)}",
            "SendGrid",
            {"to": to, "subject": subject}
        )


async def send_sms(
    to: str,
    body: str,
    from_number: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send SMS using Twilio.
    
    Args:
        to: Recipient phone number (E.164 format recommended)
        body: SMS message body
        from_number: Sender phone number (uses default if not provided)
        
    Returns:
        Dictionary with send status and message SID
        
    Raises:
        IntegrationError: If Twilio API call fails
        ValidationError: If SMS parameters are invalid
    """
    if not to:
        raise ValidationError("Recipient phone number is required")
    
    if not body:
        raise ValidationError("SMS body is required")
    
    if len(body) > 1600:
        raise ValidationError("SMS body exceeds maximum length of 1600 characters")
    
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        # Log SMS instead of sending in development
        print(f"[SMS] To: {to}, Body: {body[:100]}...")
        return {
            "success": True,
            "message_sid": "dev-mode-no-send",
            "status": "logged"
        }
    
    try:
        # Create Twilio client
        client = TwilioClient(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )
        
        # Normalize phone number (basic cleaning)
        to_number = to.strip()
        if not to_number.startswith("+"):
            # Assume US number if no country code
            to_number = f"+1{to_number.replace('-', '').replace('(', '').replace(')', '').replace(' ', '')}"
        
        from_num = from_number or settings.TWILIO_PHONE_NUMBER
        
        # Send SMS
        message = client.messages.create(
            body=body,
            from_=from_num,
            to=to_number
        )
        
        return {
            "success": True,
            "message_sid": message.sid,
            "status": message.status,
            "to": to_number,
            "from": from_num,
            "segments": message.num_segments
        }
        
    except TwilioRestException as e:
        raise IntegrationError(
            f"Twilio API error: {e.msg}",
            "Twilio",
            {"error_code": e.code, "to": to}
        )
    except Exception as e:
        raise IntegrationError(
            f"Failed to send SMS: {str(e)}",
            "Twilio",
            {"to": to}
        )


async def create_notification(
    db: Session,
    user_id: UUID,
    title: str,
    message: str,
    notification_type: str = "info",
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create an in-app notification for a user.
    
    Note: This stores notification data in a simple format.
    A proper Notification model should be created for production use.
    
    Args:
        db: Database session
        user_id: User to notify
        title: Notification title
        message: Notification message
        notification_type: Type of notification (info, success, warning, error)
        metadata: Additional metadata
        
    Returns:
        Dictionary with notification details
        
    Raises:
        ValidationError: If parameters are invalid
        DatabaseError: If database operation fails
    """
    if not title or not message:
        raise ValidationError("Notification title and message are required")
    
    valid_types = ["info", "success", "warning", "error"]
    if notification_type not in valid_types:
        raise ValidationError(
            f"Invalid notification type. Must be one of: {', '.join(valid_types)}"
        )
    
    try:
        # For now, we'll store as a simple log
        # In production, create a Notification model and table
        notification_data = {
            "id": str(UUID()),  # Generate UUID
            "user_id": str(user_id),
            "title": title,
            "message": message,
            "type": notification_type,
            "read": False,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat()
        }
        
        # TODO: Store in database when Notification model exists
        # notification = Notification(**notification_data)
        # db.add(notification)
        # db.commit()
        
        # For now, just log it
        print(f"[NOTIFICATION] User: {user_id}, Title: {title}, Type: {notification_type}")
        
        return {
            "success": True,
            **notification_data
        }
        
    except Exception as e:
        raise DatabaseError(f"Failed to create notification: {str(e)}")


async def send_notification_email(
    to: str,
    notification_type: str,
    title: str,
    message: str,
    action_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send a formatted notification email.
    
    Args:
        to: Recipient email
        notification_type: Type of notification (info, success, warning, error)
        title: Email title
        message: Email message
        action_url: Optional URL for action button
        
    Returns:
        Email send result
    """
    # Build HTML email body
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #4F46E5; color: white; padding: 20px; text-align: center; }}
            .content {{ background-color: #f9fafb; padding: 30px; }}
            .button {{ display: inline-block; padding: 12px 24px; background-color: #4F46E5; 
                      color: white; text-decoration: none; border-radius: 6px; margin-top: 20px; }}
            .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Loriaa AI</h1>
            </div>
            <div class="content">
                <h2>{title}</h2>
                <p>{message}</p>
                {f'<a href="{action_url}" class="button">View Details</a>' if action_url else ''}
            </div>
            <div class="footer">
                <p>This is an automated message from Loriaa AI. Please do not reply to this email.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Plain text version
    plain_text = f"{title}\n\n{message}"
    if action_url:
        plain_text += f"\n\nView details: {action_url}"
    
    return await send_email(
        to=to,
        subject=title,
        body=plain_text,
        html_body=html_body
    )


async def send_lead_notification(
    db: Session,
    user_id: UUID,
    lead_name: str,
    notification_type: str,
    message: str,
    send_email_notification: bool = True,
    send_sms_notification: bool = False,
    user_email: Optional[str] = None,
    user_phone: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send multi-channel notification about lead activity.
    
    Args:
        db: Database session
        user_id: User to notify
        lead_name: Name of the lead
        notification_type: Type of notification
        message: Notification message
        send_email_notification: Whether to send email
        send_sms_notification: Whether to send SMS
        user_email: User's email address
        user_phone: User's phone number
        
    Returns:
        Dictionary with results from all notification channels
    """
    results = {}
    
    # Create in-app notification
    title = f"Lead Update: {lead_name}"
    in_app = await create_notification(
        db=db,
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        metadata={"lead_name": lead_name}
    )
    results["in_app"] = in_app
    
    # Send email if requested
    if send_email_notification and user_email:
        try:
            email_result = await send_notification_email(
                to=user_email,
                notification_type=notification_type,
                title=title,
                message=message
            )
            results["email"] = email_result
        except Exception as e:
            results["email"] = {"success": False, "error": str(e)}
    
    # Send SMS if requested
    if send_sms_notification and user_phone:
        try:
            sms_text = f"{title}: {message}"[:160]  # Limit to single SMS
            sms_result = await send_sms(
                to=user_phone,
                body=sms_text
            )
            results["sms"] = sms_result
        except Exception as e:
            results["sms"] = {"success": False, "error": str(e)}
    
    return results
