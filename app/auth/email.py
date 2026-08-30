"""SMTP delivery for account notifications; credentials always come from environment settings."""
from __future__ import annotations

import smtplib
from email.message import EmailMessage

from app.utils.config import get_settings


def send_welcome_email(recipient: str) -> str | None:
    """Send a welcome notification and return a non-sensitive error message, if any."""
    settings = get_settings()
    smtp_host = getattr(settings, "smtp_host", "smtp.gmail.com")
    smtp_port = getattr(settings, "smtp_port", 587)
    smtp_username = getattr(settings, "smtp_username", "")
    smtp_password = getattr(settings, "smtp_password", "")
    smtp_from_email = getattr(settings, "smtp_from_email", "")
    if not (smtp_host and smtp_username and smtp_password and smtp_from_email):
        return "Account created, but email is not configured yet. Add the SMTP/Gmail settings to .env and restart the app."
    message = EmailMessage()
    message["Subject"] = "Welcome to Vendor Proposal AI"
    message["From"] = smtp_from_email
    message["To"] = recipient
    message.set_content("Your Vendor Proposal AI account is ready. You can now sign in and begin a vendor analysis.")
    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
            server.starttls()
            # Google displays 16-character App Passwords in groups; SMTP expects the compact value.
            login_password = smtp_password.replace(" ", "") if smtp_host.lower() == "smtp.gmail.com" else smtp_password
            server.login(smtp_username, login_password)
            server.send_message(message)
    except smtplib.SMTPAuthenticationError:
        return "Gmail rejected the SMTP login. Use your full Gmail address and a new 16-character Google App Password."
    except (smtplib.SMTPConnectError, TimeoutError):
        return "Could not connect to Gmail SMTP. Confirm SMTP_HOST is smtp.gmail.com and SMTP_PORT is 587."
    except (OSError, smtplib.SMTPException):
        return "Account created, but the welcome email could not be sent. Check the SMTP/Gmail settings."
    return None
