"""Registration, verification, sessions, and password reset.

Email links are sent with SMTP when SMTP_HOST is set. Otherwise they are kept
in the server outbox so a local developer or a test can complete verification.
The link is not returned by the API.
"""

from __future__ import annotations

import logging
import re
import secrets
import smtplib
import uuid
from email.message import EmailMessage

from fastapi import Request

from app.core.config import settings
from app.schemas.auth import ProfileResponse, PublicUser, RecentActivity, SessionResponse
from app.services import auth_store
from app.services.analytics_store import activity_for_user as analytics_activity
from app.services.analytics_store import count_for_user as analytics_count
from app.services.document_store import activity_for_user as document_activity
from app.services.document_store import count_for_user as document_count
from app.services.youtube_store import account_counts

logger = logging.getLogger(__name__)

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_ATTEMPTS: dict[str, list[float]] = {}


class AuthError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def register(name: str, email: str, password: str) -> None:
    cleaned = _email(email)
    _password_rules(password)
    display = name.strip()
    if auth_store.get_user_by_email(cleaned) is not None:
        raise AuthError(409, "An account with that email already exists.")
    user_id = str(uuid.uuid4())
    auth_store.create_user(user_id, cleaned, display, password)
    _send_verification(user_id, cleaned)


def resend_verification(email: str) -> None:
    user = auth_store.get_user_by_email(_email(email))
    if user is None or user["email_verified_at"] is not None:
        return
    _send_verification(str(user["id"]), str(user["email"]))


def verify_email(token: str) -> None:
    user_id = auth_store.consume_email_token(token.strip(), "verify")
    if user_id is None:
        raise AuthError(400, "That verification link is invalid or has expired.")
    auth_store.mark_verified(user_id)


def login(email: str, password: str, request: Request) -> tuple[str, SessionResponse]:
    _limit(request, "login", 8)
    user = auth_store.get_user_by_email(_email(email))
    if user is None or not auth_store.verify_password(password, str(user["password_hash"])):
        raise AuthError(401, "The email or password is incorrect.")
    token, csrf = auth_store.create_session(str(user["id"]))
    return token, _session_from_row(user, csrf)


def logout(token: str) -> None:
    auth_store.delete_session(token)


def request_reset(email: str) -> None:
    user = auth_store.get_user_by_email(_email(email))
    if user is None:
        return
    token = secrets.token_urlsafe(32)
    auth_store.save_email_token(str(user["id"]), "reset", token, hours=1)
    link = f"{settings.frontend_origin}/reset-password?token={token}"
    _deliver(str(user["email"]), "reset", f"Reset your CreatorLens password:\n{link}")


def reset_password(token: str, password: str) -> None:
    _password_rules(password)
    user_id = auth_store.consume_email_token(token.strip(), "reset")
    if user_id is None:
        raise AuthError(400, "That reset link is invalid or has expired.")
    auth_store.set_password(user_id, password)
    auth_store.delete_user_sessions(user_id)


def session_from_cookie(token: str) -> SessionResponse:
    row = auth_store.read_session(token)
    if row is None:
        return SessionResponse(authenticated=False)
    return SessionResponse(
        authenticated=True,
        verified=row["email_verified_at"] is not None,
        csrf_token=str(row["csrf_token"]),
        user=_public_from_session(row),
    )


def require_verified(token: str, csrf_header: str, method: str) -> PublicUser:
    row = auth_store.read_session(token)
    if row is None:
        raise AuthError(401, "Sign in to continue.")
    if method not in {"GET", "HEAD", "OPTIONS"} and not secrets.compare_digest(csrf_header, str(row["csrf_token"])):
        raise AuthError(403, "The request could not be verified. Refresh the page and try again.")
    if row["email_verified_at"] is None:
        raise AuthError(403, "Verify your email before using saved analyses.")
    return _public_from_session(row)


def update_profile(user_id: str, display_name: str) -> PublicUser:
    auth_store.update_display_name(user_id, display_name.strip())
    user = auth_store.get_user_by_id(user_id)
    if user is None:
        raise AuthError(401, "Sign in to continue.")
    return _public_from_user(user)


def profile(user: PublicUser) -> ProfileResponse:
    videos, diagnoses, experiments, recent_rows = account_counts(user.id)
    recent = [
        RecentActivity(id=item["id"], kind="youtube", title=item["title"], created_at=item["created_at"])
        for item in recent_rows
    ]
    recent.extend(document_activity(user.id))
    recent.extend(analytics_activity(user.id))
    recent.sort(key=lambda item: item.created_at, reverse=True)
    return ProfileResponse(
        user=user,
        videos_analyzed=videos,
        diagnoses_saved=diagnoses,
        experiments_saved=experiments,
        documents_saved=document_count(user.id) + analytics_count(user.id),
        recent=recent[:8],
    )


def limit_public(request: Request, action: str) -> None:
    _limit(request, action, 5)


def _send_verification(user_id: str, email: str) -> None:
    token = secrets.token_urlsafe(32)
    auth_store.save_email_token(user_id, "verify", token, hours=24)
    link = f"{settings.frontend_origin}/verify-email?token={token}"
    _deliver(email, "verify", f"Verify your CreatorLens email:\n{link}")


def _deliver(recipient: str, purpose: str, body: str) -> None:
    auth_store.queue_email(recipient, purpose, body)
    if settings.smtp_host:
        _smtp(recipient, purpose, body)
        return
    if settings.app_env != "production":
        logger.warning("Email delivery is not configured. A %s message for %s is in the server outbox.", purpose, recipient)
        logger.warning("%s", body)
    else:
        logger.error("SMTP_HOST is not set, so the %s email for %s was not sent.", purpose, recipient)


def _smtp(recipient: str, purpose: str, body: str) -> None:
    message = EmailMessage()
    message["Subject"] = "Verify your CreatorLens email" if purpose == "verify" else "Reset your CreatorLens password"
    message["From"] = settings.smtp_from or settings.smtp_username
    message["To"] = recipient
    message.set_content(body)
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as client:
            if settings.smtp_tls:
                client.starttls()
            if settings.smtp_username:
                client.login(settings.smtp_username, settings.smtp_password)
            client.send_message(message)
    except OSError:
        logger.exception("The %s email could not be sent.", purpose)


def _session_from_row(user, csrf: str) -> SessionResponse:
    return SessionResponse(
        authenticated=True,
        verified=user["email_verified_at"] is not None,
        csrf_token=csrf,
        user=_public_from_user(user),
    )


def _public_from_user(user) -> PublicUser:
    return PublicUser(
        id=str(user["id"]),
        email=str(user["email"]),
        display_name=str(user["display_name"]),
        email_verified=user["email_verified_at"] is not None,
        created_at=str(user["created_at"]),
    )


def _public_from_session(row) -> PublicUser:
    return PublicUser(
        id=str(row["user_id"]),
        email=str(row["email"]),
        display_name=str(row["display_name"]),
        email_verified=row["email_verified_at"] is not None,
        created_at=str(row["created_at"]),
    )


def _email(value: str) -> str:
    cleaned = value.strip().lower()
    if _EMAIL.fullmatch(cleaned) is None:
        raise AuthError(400, "Enter a valid email address.")
    return cleaned


def _password_rules(password: str) -> None:
    if len(password) < 10 or not any(character.isalpha() for character in password) or not any(character.isdigit() for character in password):
        raise AuthError(400, "Use at least 10 characters, including a letter and a number.")


def _limit(request: Request, action: str, maximum: int) -> None:
    import time

    host = request.client.host if request.client else "unknown"
    key = f"{action}:{host}"
    now = time.monotonic()
    window = [stamp for stamp in _ATTEMPTS.get(key, []) if now - stamp < 600]
    if len(window) >= maximum:
        raise AuthError(429, "Too many attempts. Wait a few minutes and try again.")
    window.append(now)
    _ATTEMPTS[key] = window
