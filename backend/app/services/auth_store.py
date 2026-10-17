"""Accounts, sessions, and one-time email tokens. Passwords are never stored."""

from __future__ import annotations

import hashlib
import hmac
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone

from app.core.config import settings

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    email_verified_at TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    csrf_token TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS email_tokens (
    token_hash TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    purpose TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    used_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS email_outbox (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipient TEXT NOT NULL,
    purpose TEXT NOT NULL,
    body TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""

PBKDF2_ITERATIONS = 600_000


def _connect() -> sqlite3.Connection:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(settings.data_dir / "auth.sqlite", timeout=10)
    connection.row_factory = sqlite3.Row
    connection.executescript(_SCHEMA)
    return connection


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, iterations, salt_hex, digest_hex = stored.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        rounds = int(iterations)
    except ValueError:
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), rounds)
    return hmac.compare_digest(digest.hex(), digest_hex)


def create_user(user_id: str, email: str, display_name: str, password: str) -> None:
    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO users (id, email, display_name, password_hash, email_verified_at, created_at)
            VALUES (?, ?, ?, ?, NULL, ?)
            """,
            (user_id, email, display_name, hash_password(password), _now().isoformat()),
        )


def get_user_by_email(email: str) -> sqlite3.Row | None:
    with _connect() as connection:
        return connection.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()


def get_user_by_id(user_id: str) -> sqlite3.Row | None:
    with _connect() as connection:
        return connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def update_display_name(user_id: str, display_name: str) -> None:
    with _connect() as connection:
        connection.execute("UPDATE users SET display_name = ? WHERE id = ?", (display_name, user_id))


def mark_verified(user_id: str) -> None:
    with _connect() as connection:
        connection.execute(
            "UPDATE users SET email_verified_at = ? WHERE id = ? AND email_verified_at IS NULL",
            (_now().isoformat(), user_id),
        )


def set_password(user_id: str, password: str) -> None:
    with _connect() as connection:
        connection.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (hash_password(password), user_id),
        )


def save_email_token(user_id: str, purpose: str, token: str, hours: int) -> None:
    expires = (_now() + timedelta(hours=hours)).isoformat()
    with _connect() as connection:
        connection.execute(
            "DELETE FROM email_tokens WHERE user_id = ? AND purpose = ? AND used_at IS NULL",
            (user_id, purpose),
        )
        connection.execute(
            """
            INSERT INTO email_tokens (token_hash, user_id, purpose, expires_at, used_at)
            VALUES (?, ?, ?, ?, NULL)
            """,
            (_hash_token(token), user_id, purpose, expires),
        )


def consume_email_token(token: str, purpose: str) -> str | None:
    token_hash = _hash_token(token)
    now = _now().isoformat()
    with _connect() as connection:
        row = connection.execute(
            """
            SELECT user_id, expires_at, used_at FROM email_tokens
            WHERE token_hash = ? AND purpose = ?
            """,
            (token_hash, purpose),
        ).fetchone()
        if row is None or row["used_at"] is not None:
            return None
        if row["expires_at"] < now:
            return None
        connection.execute("UPDATE email_tokens SET used_at = ? WHERE token_hash = ?", (now, token_hash))
    return str(row["user_id"])


def create_session(user_id: str) -> tuple[str, str]:
    token = secrets.token_urlsafe(32)
    csrf = secrets.token_urlsafe(32)
    expires = (_now() + timedelta(days=14)).isoformat()
    with _connect() as connection:
        connection.execute(
            "INSERT INTO sessions (token_hash, user_id, csrf_token, expires_at) VALUES (?, ?, ?, ?)",
            (_hash_token(token), user_id, csrf, expires),
        )
    return token, csrf


def read_session(token: str) -> sqlite3.Row | None:
    if not token:
        return None
    now = _now().isoformat()
    with _connect() as connection:
        row = connection.execute(
            """
            SELECT sessions.user_id, sessions.csrf_token, sessions.expires_at,
                   users.email, users.display_name, users.email_verified_at, users.created_at
            FROM sessions JOIN users ON users.id = sessions.user_id
            WHERE sessions.token_hash = ?
            """,
            (_hash_token(token),),
        ).fetchone()
    if row is None or row["expires_at"] < now:
        return None
    return row


def delete_session(token: str) -> None:
    if not token:
        return
    with _connect() as connection:
        connection.execute("DELETE FROM sessions WHERE token_hash = ?", (_hash_token(token),))


def delete_user_sessions(user_id: str) -> None:
    with _connect() as connection:
        connection.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))


def queue_email(recipient: str, purpose: str, body: str) -> None:
    with _connect() as connection:
        connection.execute(
            "INSERT INTO email_outbox (recipient, purpose, body, created_at) VALUES (?, ?, ?, ?)",
            (recipient, purpose, body, _now().isoformat()),
        )


def latest_email_body(recipient: str, purpose: str) -> str | None:
    with _connect() as connection:
        row = connection.execute(
            """
            SELECT body FROM email_outbox
            WHERE recipient = ? AND purpose = ?
            ORDER BY id DESC LIMIT 1
            """,
            (recipient, purpose),
        ).fetchone()
    if row is None:
        return None
    return str(row["body"])
