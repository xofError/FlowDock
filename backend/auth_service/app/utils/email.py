import os
import smtplib
from email.message import EmailMessage
from typing import Optional


def send_email(to: str, subject: str, body: str) -> None:
    """Send an email using SMTP if configured, otherwise print to console.

    Environment variables used for SMTP: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS
    If SMTP_HOST is not set the function will print the message to stdout (useful for local dev).
    """
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "25"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")

    msg = EmailMessage()
    msg["From"] = os.getenv("EMAIL_FROM", "noreply@example.com")
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    if not smtp_host:
        # No SMTP configured — fall back to console logging for development
        print("--- Email (dev) ---")
        print(f"To: {to}")
        print(f"Subject: {subject}")
        print(body)
        print("--- End Email ---")
        return

    with smtplib.SMTP(host=smtp_host, port=smtp_port) as server:
        server.ehlo()
        if smtp_user and smtp_pass:
            server.starttls()
            server.login(smtp_user, smtp_pass)
        server.send_message(msg)