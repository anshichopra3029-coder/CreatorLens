"""SQLite store for processed analytics CSV analyses. The raw upload is not kept."""

from __future__ import annotations

import json
import sqlite3

from app.core.config import settings
from app.schemas.analytics import AnalyticsAnalysisResponse, AnalyticsListItem
from app.schemas.auth import RecentActivity
from app.services.ownership import ensure_owner_column

_SCHEMA = """
CREATE TABLE IF NOT EXISTS analytics_analyses (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    payload TEXT NOT NULL
);
"""


def _connect() -> sqlite3.Connection:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(settings.data_dir / "analytics.sqlite", timeout=10)
    connection.row_factory = sqlite3.Row
    connection.executescript(_SCHEMA)
    ensure_owner_column(connection, "analytics_analyses")
    return connection


def insert_analysis(record: AnalyticsAnalysisResponse, user_id: str) -> None:
    with _connect() as connection:
        connection.execute(
            "INSERT INTO analytics_analyses (id, created_at, payload, user_id) VALUES (?, ?, ?, ?)",
            (record.id, record.created_at, record.model_dump_json(), user_id),
        )


def get_analysis(analysis_id: str, user_id: str) -> AnalyticsAnalysisResponse | None:
    del user_id
    with _connect() as connection:
        row = connection.execute(
            "SELECT payload FROM analytics_analyses WHERE id = ?",
            (analysis_id,),
        ).fetchone()
    if row is None:
        return None
    return AnalyticsAnalysisResponse.model_validate_json(row["payload"])


def list_analyses(user_id: str) -> list[AnalyticsListItem]:
    del user_id
    with _connect() as connection:
        rows = connection.execute(
            "SELECT payload FROM analytics_analyses ORDER BY created_at DESC",
        ).fetchall()
    items: list[AnalyticsListItem] = []
    for row in rows:
        record = AnalyticsAnalysisResponse.model_validate_json(row["payload"])
        items.append(
            AnalyticsListItem(
                id=record.id,
                filename=record.filename,
                created_at=record.created_at,
                video_count=record.summary.video_count,
                observation_count=record.summary.observation_count,
                total_latest_views=record.summary.total_latest_views,
                average_engagement_rate=record.summary.average_engagement_rate,
                prediction_eligible=record.prediction.eligible,
                prediction_message=record.prediction.message,
            )
        )
    return items


def count_for_user(user_id: str) -> int:
    del user_id
    with _connect() as connection:
        row = connection.execute(
            "SELECT COUNT(*) AS total FROM analytics_analyses",
        ).fetchone()
    return int(row["total"]) if row is not None else 0


def activity_for_user(user_id: str) -> list[RecentActivity]:
    del user_id
    with _connect() as connection:
        rows = connection.execute(
            "SELECT id, payload, created_at FROM analytics_analyses ORDER BY created_at DESC LIMIT 5",
        ).fetchall()
    items: list[RecentActivity] = []
    for row in rows:
        record = AnalyticsAnalysisResponse.model_validate_json(row["payload"])
        items.append(RecentActivity(id=record.id, kind="analytics", title=record.filename, created_at=record.created_at))
    return items
