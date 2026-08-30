"""Credential operations behind a small interface that can later use a database."""
from __future__ import annotations

import base64
import hashlib
import hmac
import re
import secrets

from app.persistence.database import create_user, get_user, update_last_login

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LENGTH = 8


def validate_email(email: str) -> str | None:
    if not email.strip():
        return "Email is required."
    if not EMAIL_PATTERN.fullmatch(email.strip()):
        return "Enter a valid email address."
    return None


def validate_password(password: str) -> str | None:
    if not password:
        return "Password is required."
    if len(password) < MIN_PASSWORD_LENGTH:
        return f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
    if not any(char.isalpha() for char in password) or not any(char.isdigit() for char in password):
        return "Password must include at least one letter and one number."
    return None


def _hash_password(password: str, salt: bytes) -> str:
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 310_000)
    return base64.b64encode(digest).decode("ascii")


def create_account(email: str, password: str) -> str | None:
    """Create a durable local account; return an error or None on success."""
    normalized_email = email.strip().lower()
    error = validate_email(normalized_email) or validate_password(password)
    if error:
        return error
    salt = secrets.token_bytes(16)
    created = create_user(
        normalized_email,
        base64.b64encode(salt).decode("ascii"),
        _hash_password(password, salt),
    )
    if not created:
        return "An account already exists for this email. Please log in instead."
    return None


def verify_credentials(email: str, password: str) -> str | None:
    """Verify an account without storing or displaying plain passwords."""
    normalized_email = email.strip().lower()
    error = validate_email(normalized_email)
    if error:
        return error
    if not password:
        return "Password is required."
    account = get_user(normalized_email)
    if account is None:
        return "Incorrect email or password."
    salt = base64.b64decode(account["password_salt"])
    candidate_hash = _hash_password(password, salt)
    if not hmac.compare_digest(candidate_hash, account["password_hash"]):
        return "Incorrect email or password."
    update_last_login(normalized_email)
    return None
