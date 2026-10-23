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
CREATE TABLE IF NOT EXISTS view_observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    video_id TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    views INTEGER NOT NULL,
    source TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (user_id, video_id, observed_at)
);
CREATE INDEX IF NOT EXISTS idx_view_observations_video ON view_observations (user_id, video_id, observed_at);
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


def analyses_for_video(video_id: str, user_id: str) -> list[YoutubeAnalysisResponse]:
    del user_id
    with _connect() as connection:
        rows = connection.execute(
            "SELECT payload FROM youtube_analyses WHERE video_id = ? ORDER BY created_at ASC",
            (video_id,),
        ).fetchall()
    return [YoutubeAnalysisResponse.model_validate_json(row["payload"]) for row in rows]


def insert_observations(user_id: str, video_id: str, rows: list[tuple[str, int]], source: str) -> tuple[int, int]:
    """Insert dated view counts. A timestamp already stored for this video is skipped, not overwritten."""
    inserted = 0
    created = _now().replace(microsecond=0).isoformat()
    with _connect() as connection:
        for observed_at, views in rows:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO view_observations (user_id, video_id, observed_at, views, source, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, video_id, observed_at, int(views), source, created),
            )
            inserted += cursor.rowcount
    return inserted, len(rows) - inserted


def stored_observations(video_id: str, user_id: str) -> list[tuple[str, int, str]]:
    with _connect() as connection:
        rows = connection.execute(
            "SELECT observed_at, views, source FROM view_observations WHERE user_id = ? AND video_id = ? ORDER BY observed_at",
            (user_id, video_id),
        ).fetchall()
    return [(str(row["observed_at"]), int(row["views"]), str(row["source"])) for row in rows]


def observation_points(video_id: str, user_id: str) -> list[tuple[str, int, str]]:
    """Saved snapshots plus imported or collected counts, oldest first.

    An analysis built from cached metadata repeats an earlier fetch. When its
    counts match the previous analysis, it is not counted as a new observation.
    """
    points: list[tuple[str, int, str]] = []
    previous: tuple[int | None, int | None, int | None] | None = None
    for record in analyses_for_video(video_id, user_id):
        counts = (record.statistics.views, record.statistics.likes, record.statistics.comments)
        repeated = record.cached_metadata and previous == counts
        previous = counts
        if repeated or record.statistics.views is None:
            continue
        points.append((record.created_at, record.statistics.views, "analysis"))
    points.extend(stored_observations(video_id, user_id))
    points.sort(key=lambda item: item[0])
    return points


def tracked_videos(user_id: str) -> list[dict[str, object]]:
    with _connect() as connection:
        rows = connection.execute(
            "SELECT video_id, payload FROM youtube_analyses ORDER BY created_at ASC",
        ).fetchall()
    grouped: dict[str, list[YoutubeAnalysisResponse]] = {}
    for row in rows:
        grouped.setdefault(str(row["video_id"]), []).append(YoutubeAnalysisResponse.model_validate_json(row["payload"]))
    items: list[dict[str, object]] = []
    for video_id, records in grouped.items():
        latest = records[-1]
        points = observation_points(video_id, user_id)
        items.append(
            {
                "video_id": video_id,
                "title": latest.metadata.title,
                "channel_title": latest.metadata.channel_title,
                "thumbnail_url": latest.metadata.thumbnail_url,
                "latest_analysis_id": latest.id,
                "analyses": len(records),
                "observations": len({stamp for stamp, _, _ in points}),
                "latest_observed_at": points[-1][0] if points else None,
                "latest_views": points[-1][1] if points else None,
            }
        )
    items.sort(key=lambda item: str(item["latest_observed_at"] or ""), reverse=True)
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
