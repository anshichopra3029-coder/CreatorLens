"""SQLite store for YouTube metadata snapshots and saved analyses."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

from app.core.config import settings
from app.schemas.youtube import YoutubeAnalysisResponse, YoutubeListItem
from app.services.ownership import ensure_owner_column

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
    ensure_owner_column(connection, "youtube_analyses")
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


def latest_channel_peers(
    channel_id: str | None,
    exclude_video_id: str,
    user_id: str,
) -> list[dict[str, str | float | None]]:
    """Latest saved engagement rate for this user's other videos on the same channel."""
    if not channel_id:
        return []
    del user_id
    with _connect() as connection:
        rows = connection.execute(
            "SELECT payload FROM youtube_analyses ORDER BY created_at ASC",
        ).fetchall()
    latest: dict[str, YoutubeAnalysisResponse] = {}
    for row in rows:
        record = YoutubeAnalysisResponse.model_validate_json(row["payload"])
        if record.metadata.channel_id != channel_id or record.metadata.video_id == exclude_video_id:
            continue
        latest[record.metadata.video_id] = record
    return [
        {
            "video_id": record.metadata.video_id,
            "title": record.metadata.title,
            "engagement_rate": record.statistics.engagement_rate,
        }
        for record in latest.values()
    ]


def snapshot_points(video_id: str, user_id: str) -> list[tuple[str, int | None]]:
    del user_id
    with _connect() as connection:
        rows = connection.execute(
            "SELECT payload FROM youtube_analyses WHERE video_id = ? ORDER BY created_at ASC",
            (video_id,),
        ).fetchall()
    points: list[tuple[str, int | None]] = []
    for row in rows:
        record = YoutubeAnalysisResponse.model_validate_json(row["payload"])
        points.append((record.created_at, record.statistics.views))
    return points


def insert_analysis(record: YoutubeAnalysisResponse, user_id: str) -> None:
    with _connect() as connection:
        connection.execute(
            "INSERT INTO youtube_analyses (id, video_id, created_at, payload, user_id) VALUES (?, ?, ?, ?, ?)",
            (
                record.id,
                record.metadata.video_id,
                record.created_at,
                record.model_dump_json(),
                user_id,
            ),
        )


def save_analysis(record: YoutubeAnalysisResponse, user_id: str) -> None:
    del user_id
    with _connect() as connection:
        updated = connection.execute(
            "UPDATE youtube_analyses SET payload = ? WHERE id = ?",
            (record.model_dump_json(), record.id),
        )
        if updated.rowcount != 1:
            raise RuntimeError("The saved analysis could not be updated.")


def get_analysis(analysis_id: str, user_id: str) -> YoutubeAnalysisResponse | None:
    del user_id
    with _connect() as connection:
        row = connection.execute(
            "SELECT payload FROM youtube_analyses WHERE id = ?",
            (analysis_id,),
        ).fetchone()
    if row is None:
        return None
    return YoutubeAnalysisResponse.model_validate_json(row["payload"])


def list_analyses(user_id: str) -> list[YoutubeListItem]:
    with _connect() as connection:
        rows = connection.execute(
            "SELECT payload FROM youtube_analyses ORDER BY created_at DESC",
        ).fetchall()
    del user_id
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
                views_per_day=record.views_per_day,
                prediction_eligible=record.prediction.eligible,
                prediction_message=record.prediction.message,
            )
        )
    return items


def account_counts(user_id: str) -> tuple[int, int, int, list[dict[str, str]]]:
    with _connect() as connection:
        rows = connection.execute(
            "SELECT payload FROM youtube_analyses ORDER BY created_at DESC",
        ).fetchall()
    del user_id
    videos = 0
    diagnoses = 0
    experiments = 0
    recent: list[dict[str, str]] = []
    for row in rows:
        record = YoutubeAnalysisResponse.model_validate_json(row["payload"])
        videos += 1
        if record.diagnosis is not None:
            diagnoses += 1
        if record.experiment is not None:
            experiments += 1
        if len(recent) < 5:
            recent.append(
                {"id": record.id, "title": record.metadata.title, "created_at": record.created_at}
            )
    return videos, diagnoses, experiments, recent
