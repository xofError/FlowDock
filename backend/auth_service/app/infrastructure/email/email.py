"""
Infrastructure Layer: Email Service

Abstraction for sending emails (SMTP or console fallback).
"""

import os
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class IEmailService(ABC):
    """Interface for email sending."""

    @abstractmethod
    def send(self, to: str, subject: str, body: str) -> bool:
        """Send an email. Returns True on success."""
        pass


class SMTPEmailService(IEmailService):
    """SMTP email service implementation."""

    def __init__(self, smtp_host: str = None, smtp_port: int = None, 
                 smtp_user: str = None, smtp_password: str = None, 
                 from_email: str = None):
        self.smtp_host = smtp_host or os.getenv("SMTP_HOST")
        self.smtp_port = int(smtp_port or os.getenv("SMTP_PORT", 587))
        self.smtp_user = smtp_user or os.getenv("SMTP_USER")
        self.smtp_password = smtp_password or os.getenv("SMTP_PASSWORD")
        self.from_email = from_email or os.getenv("SMTP_FROM_EMAIL", "noreply@flowdock.local")

    def send(self, to: str, subject: str, body: str) -> bool:
        """Send email via SMTP."""
        if not self.smtp_host:
            logger.warning(f"SMTP not configured. Would send email to {to}")
            return True

        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            msg = MIMEMultipart()
            msg["From"] = self.from_email
            msg["To"] = to
            msg["Subject"] = subject

            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_user and self.smtp_password:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent to {to}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to}: {e}")
            return False


class ConsoleEmailService(IEmailService):
    """Console email service for development - prints emails to logs."""

    def send(self, to: str, subject: str, body: str) -> bool:
        """Print email to console/logs."""
        logger.info(f"""
        ===== EMAIL =====
        TO: {to}
        SUBJECT: {subject}
        BODY:
        {body}
        =================
        """)
        return True


def get_email_service() -> IEmailService:
    """Factory function to get appropriate email service."""
    if os.getenv("SMTP_HOST"):
        return SMTPEmailService()
    else:
        return ConsoleEmailService()
