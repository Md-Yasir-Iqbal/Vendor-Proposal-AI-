"""SMTP delivery for account notifications; credentials always come from environment settings."""
from __future__ import annotations

import smtplib
from email.message import EmailMessage

from app.utils.config import get_settings


def send_welcome_email(recipient: str) -> str | None:
    """Send a welcome notification and return a non-sensitive error message, if any."""
    settings = get_settings()
    if not settings.is_smtp_configured():
        return "Account created, but email is not configured yet. Add the SMTP/Gmail settings to .env and restart the app."
    message = EmailMessage()
    message["Subject"] = "Welcome to Vendor Proposal AI"
    message["From"] = settings.smtp_from_email
    message["To"] = recipient
    message.set_content("Your Vendor Proposal AI account is ready. You can now sign in and begin a vendor analysis.")
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
            server.starttls()
            server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(message)
    except (OSError, smtplib.SMTPException):
        return "Account created, but the welcome email could not be sent. Check the SMTP/Gmail settings."
    return None
