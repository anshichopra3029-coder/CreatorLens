"""SQLite store for YouTube metadata snapshots and saved analyses."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

from app.core.config import settings
from app.schemas.youtube import YoutubeAnalysisResponse, YoutubeListItem

_SCHEMA = """
CREATE TABLE IF NOT EXISTS youtube_analyses (
    id TEXT PRIMARY KEY,
    video_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    payload TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS youtube_cache (
    video_id TEXT PRIMARY KEY,
    fetched_at TEXT NOT NULL,
    payload TEXT NOT NULL
);
"""


def _connect() -> sqlite3.Connection:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(settings.data_dir / "youtube.sqlite", timeout=10)
    connection.row_factory = sqlite3.Row
    connection.executescript(_SCHEMA)
    return connection


def _now() -> datetime:
    return datetime.now(timezone.utc)


def get_cached_video(video_id: str) -> dict | None:
    with _connect() as connection:
        row = connection.execute(
            "SELECT fetched_at, payload FROM youtube_cache WHERE video_id = ?",
            (video_id,),
        ).fetchone()
    if row is None:
        return None
    fetched = datetime.fromisoformat(row["fetched_at"])
    age = (_now() - fetched).total_seconds()
    if age > settings.youtube_cache_seconds:
        return None
    payload = json.loads(row["payload"])
    return payload if isinstance(payload, dict) else None


def put_cached_video(video_id: str, payload: dict) -> None:
    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO youtube_cache (video_id, fetched_at, payload)
            VALUES (?, ?, ?)
            ON CONFLICT(video_id) DO UPDATE SET fetched_at = excluded.fetched_at, payload = excluded.payload
            """,
            (video_id, _now().replace(microsecond=0).isoformat(), json.dumps(payload)),
        )


def insert_analysis(record: YoutubeAnalysisResponse) -> None:
    with _connect() as connection:
        connection.execute(
            "INSERT INTO youtube_analyses (id, video_id, created_at, payload) VALUES (?, ?, ?, ?)",
            (
                record.id,
                record.metadata.video_id,
                record.created_at,
                record.model_dump_json(),
            ),
        )


def get_analysis(analysis_id: str) -> YoutubeAnalysisResponse | None:
    with _connect() as connection:
        row = connection.execute(
            "SELECT payload FROM youtube_analyses WHERE id = ?",
            (analysis_id,),
        ).fetchone()
    if row is None:
        return None
    return YoutubeAnalysisResponse.model_validate_json(row["payload"])


def list_analyses() -> list[YoutubeListItem]:
    with _connect() as connection:
        rows = connection.execute(
            "SELECT payload FROM youtube_analyses ORDER BY created_at DESC"
        ).fetchall()
    items: list[YoutubeListItem] = []
    for row in rows:
        record = YoutubeAnalysisResponse.model_validate_json(row["payload"])
        items.append(
            YoutubeListItem(
                id=record.id,
                video_id=record.metadata.video_id,
                title=record.metadata.title,
                channel_title=record.metadata.channel_title,
                thumbnail_url=record.metadata.thumbnail_url,
                created_at=record.created_at,
                views=record.statistics.views,
                likes=record.statistics.likes,
                comments=record.statistics.comments,
                engagement_rate=record.statistics.engagement_rate,
            )
        )
    return items
