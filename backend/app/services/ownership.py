"""Add an owner column without giving old rows to a new account.

SQLite has no row-level security. Every private query also filters on user_id.
Rows whose user_id is NULL stay in the database and match no account.
"""

from __future__ import annotations

import sqlite3


def ensure_owner_column(connection: sqlite3.Connection, table: str) -> None:
    columns = {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}
    if "user_id" not in columns:
        connection.execute(f"ALTER TABLE {table} ADD COLUMN user_id TEXT")
    connection.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_user_id ON {table} (user_id)")
