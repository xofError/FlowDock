import os
import smtplib
from email.message import EmailMessage
from typing import Optional


def send_email(to: str, subject: str, body: str) -> None:
    """Send an email using SMTP if configured, otherwise print to console.

    Environment variables used for SMTP: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS
    If SMTP_HOST is not set the function will print the message to stdout (useful for local dev).
    """
    # smtp_host = os.getenv("SMTP_HOST")
    # smtp_port = int(os.getenv("SMTP_PORT", "25"))
    # smtp_user = os.getenv("SMTP_USER")
    # smtp_pass = os.getenv("SMTP_PASS")

    msg = EmailMessage()
    msg["From"] ="flowdockproduction@gmail.com"
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

# if not smtp_host:
    # No SMTP configured — fall back to console logging for development
    print("--- Email (dev) ---")
    print(f"To: {to}")
    print(f"Subject: {subject}")
    print(body)
    print("--- End Email ---")


    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login("flowdockproduction@gmail.com", "hmlz qbkb rbbb npja")
        smtp.send_message(msg)