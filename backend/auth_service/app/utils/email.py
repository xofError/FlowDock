"""
Email Utility - Wrapper around Infrastructure Email Service

This module provides backward compatibility with the old email interface
while using the new clean architecture email service internally.
"""

from app.infrastructure.email.email import get_email_service


def send_email(to: str, subject: str, body: str) -> None:
    """
    Send an email using configured email service.
    
    Environment variables for SMTP: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM_EMAIL
    If SMTP_HOST is not set, emails are printed to console for development.
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body text
    """
    email_service = get_email_service()
    email_service.send(to, subject, body)

        
