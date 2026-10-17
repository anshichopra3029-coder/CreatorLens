"""Public YouTube metadata through yt-dlp.

``extract_info(..., download=False)`` reads metadata only. The video file is
not downloaded. Private and login-gated videos are rejected. Comment text is
not requested; a comment count is kept only when the extractor returns one.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from app.schemas.youtube import PublicStatistics, VideoMetadata
from app.services.youtube_urls import canonical_watch_url

Extractor = Callable[[str], dict[str, Any]]

TRANSCRIPT_REASON = (
    "No transcript was retrieved. Metadata extraction does not watch the video "
    "or download captions."
)
ANALYTICS_REASON = (
    "Impressions, click-through rate, and audience retention require the creator's "
    "YouTube Analytics authorization. That connection is not set up, so no retention curve is stored."
)
COMMENT_TEXT_REASON = (
    "Comment text was not retrieved. Metadata extraction records a comment count "
    "only when the extractor returns one."
)
RESTRICTED = {"private", "needs_auth", "premium_only", "subscriber_only", "login_required"}


class YoutubeApiError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def fetch_video(video_id: str, *, extractor: Extractor | None = None) -> tuple[VideoMetadata, PublicStatistics]:
    url = canonical_watch_url(video_id)
    try:
        info = extractor(url) if extractor is not None else _extract(url)
    except YoutubeApiError:
        raise
    except Exception as exc:
        raise _from_exception(exc) from exc
    if not isinstance(info, dict):
        raise YoutubeApiError(502, "Metadata extraction returned a response that could not be read.")
    return _metadata(video_id, info), _statistics(info)


def comment_text_status() -> tuple[str, list]:
    return "unavailable", []


def transcript_status():
    from app.schemas.youtube import TranscriptStatus

    return TranscriptStatus(available=False, text="", reason=TRANSCRIPT_REASON)


def analytics_status():
    from app.schemas.youtube import AnalyticsAvailability

    return AnalyticsAvailability(
        connected=False,
        impressions=None,
        click_through_rate=None,
        audience_retention=None,
        reason=ANALYTICS_REASON,
    )


def _extract(url: str) -> dict[str, Any]:
    import yt_dlp

    options = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": True,
        "socket_timeout": 20,
        "retries": 1,
        "extractor_retries": 1,
        "logger": _QuietLogger(),
    }
    with yt_dlp.YoutubeDL(options) as downloader:
        info = downloader.extract_info(url, download=False)
    if not isinstance(info, dict):
        raise YoutubeApiError(502, "Metadata extraction returned a response that could not be read.")
    return info


class _QuietLogger:
    def debug(self, message: str) -> None:
        return None

    def info(self, message: str) -> None:
        return None

    def warning(self, message: str) -> None:
        return None

    def error(self, message: str) -> None:
        return None


def _from_exception(exc: Exception) -> YoutubeApiError:
    text = str(exc).lower()
    if "sign in to confirm" in text or "not a bot" in text:
        return YoutubeApiError(
            503,
            "YouTube blocked the metadata request with a sign-in check. No new statistics were saved.",
        )
    if any(word in text for word in ("private", "unavailable", "removed", "deleted", "not available")):
        return YoutubeApiError(404, "That video is private, deleted, or unavailable. No statistics were saved.")
    if any(word in text for word in ("429", "rate-limit", "rate limit", "too many")):
        return YoutubeApiError(429, "YouTube rate-limited the metadata request. No new statistics were retrieved.")
    if any(word in text for word in ("timed out", "timeout", "network", "connection", "temporary failure")):
        return YoutubeApiError(504, "The metadata request timed out. No statistics were saved.")
    return YoutubeApiError(502, "Metadata extraction failed. No statistics were saved.")


def _metadata(video_id: str, info: dict[str, Any]) -> VideoMetadata:
    returned = str(info.get("id") or "")
    if returned and returned != video_id:
        raise YoutubeApiError(502, "The extractor returned a different video than the URL.")
    availability = str(info.get("availability") or "public")
    if availability in RESTRICTED:
        raise YoutubeApiError(404, "That video is not public, so its statistics were not analysed.")
    categories = info.get("categories") if isinstance(info.get("categories"), list) else []
    tags = info.get("tags") if isinstance(info.get("tags"), list) else []
    category = str(categories[0])[:80] if categories else None
    clean_tags = [str(tag)[:80] for tag in tags[:20] if str(tag).strip()]
    thumbnail = info.get("thumbnail")
    if not isinstance(thumbnail, str) or thumbnail.strip() == "":
        thumbnail = None
    channel_id = str(info.get("channel_id") or info.get("uploader_id") or "")[:80] or None
    return VideoMetadata(
        video_id=video_id,
        url=canonical_watch_url(video_id),
        title=str(info.get("title") or "Untitled video")[:300],
        description=str(info.get("description") or "")[:5000],
        channel_title=str(info.get("channel") or info.get("uploader") or "Unknown channel")[:200],
        channel_id=channel_id,
        thumbnail_url=thumbnail,
        published_at=_published(info),
        duration_seconds=_duration(info.get("duration")),
        privacy_status=availability[:40] or "public",
        category=category,
        tags=clean_tags,
    )


def _statistics(info: dict[str, Any]) -> PublicStatistics:
    views = _count(info, "view_count")
    likes = _count(info, "like_count")
    comments = _count(info, "comment_count")
    rate = None
    if views is not None and likes is not None and comments is not None and views > 0:
        rate = round((likes + comments) / views * 100, 2)
    return PublicStatistics(
        views=views,
        likes=likes,
        comments=comments,
        views_available=views is not None,
        likes_available=likes is not None,
        comments_available=comments is not None,
        engagement_rate=rate,
    )


def _count(info: dict[str, Any], key: str) -> int | None:
    if key not in info or info[key] is None or info[key] == "":
        return None
    try:
        number = int(info[key])
    except (TypeError, ValueError):
        return None
    if number < 0:
        return None
    return number


def _duration(value: object) -> int | None:
    if value is None or value == "":
        return None
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    if number < 0:
        return None
    return number


def _published(info: dict[str, Any]) -> str | None:
    raw = info.get("upload_date") or info.get("release_date")
    if isinstance(raw, str) and len(raw) == 8 and raw.isdigit():
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}T00:00:00+00:00"
    timestamp = info.get("timestamp") or info.get("release_timestamp")
    if isinstance(timestamp, (int, float)) and timestamp > 0:
        return datetime.fromtimestamp(timestamp, timezone.utc).replace(microsecond=0).isoformat()
    return None
