"""Official YouTube Data API reads.

Captions and YouTube Analytics are not requested with the API key. Caption
download and audience retention require the video owner's OAuth grant.
"""

from __future__ import annotations

import re
from typing import Any, Callable

import httpx

from app.core.config import settings
from app.schemas.youtube import AnalyticsAvailability, CommentSnippet, PublicStatistics, TranscriptStatus, VideoMetadata
from app.services.youtube_urls import canonical_watch_url

VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"
COMMENTS_URL = "https://www.googleapis.com/youtube/v3/commentThreads"
Fetcher = Callable[[str, dict[str, str]], tuple[int, dict[str, Any]]]

MISSING_YOUTUBE_KEY = (
    "YOUTUBE_API_KEY is not configured on the server. "
    "No YouTube data was requested, and no statistics were generated."
)
TRANSCRIPT_REASON = (
    "No transcript was retrieved. The official captions download requires the video owner's "
    "YouTube OAuth grant, which is not connected. The analysis did not watch the video."
)
ANALYTICS_REASON = (
    "Impressions, click-through rate, and audience retention require the creator's "
    "YouTube Analytics authorization. That connection is not set up, so no retention curve is stored."
)


class YoutubeApiError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def require_youtube_key() -> None:
    if not settings.youtube_api_key:
        raise YoutubeApiError(503, MISSING_YOUTUBE_KEY)


def fetch_video(video_id: str, *, fetcher: Fetcher | None = None) -> tuple[VideoMetadata, PublicStatistics]:
    require_youtube_key()
    status, payload = _request(
        VIDEOS_URL,
        {"part": "snippet,contentDetails,statistics,status", "id": video_id},
        fetcher,
    )
    _raise_for_api_status(status, payload)
    items = payload.get("items") if isinstance(payload, dict) else None
    if not isinstance(items, list) or len(items) == 0:
        raise YoutubeApiError(404, "YouTube did not return that video. It may be private, deleted, or unavailable.")
    item = items[0]
    if not isinstance(item, dict):
        raise YoutubeApiError(502, "YouTube returned a response that could not be read.")
    privacy = str((item.get("status") or {}).get("privacyStatus") or "")
    if privacy and privacy != "public":
        raise YoutubeApiError(404, "That video is not public, so its statistics were not analysed.")
    return _metadata(video_id, item), _statistics(item.get("statistics") or {})


def fetch_comments(
    video_id: str, *, fetcher: Fetcher | None = None
) -> tuple[str, list[CommentSnippet]]:
    require_youtube_key()
    status, payload = _request(
        COMMENTS_URL,
        {
            "part": "snippet",
            "videoId": video_id,
            "maxResults": "15",
            "order": "relevance",
            "textFormat": "plainText",
        },
        fetcher,
    )
    reason = _error_reason(payload)
    if status == 403 and reason == "commentsDisabled":
        return "disabled", []
    if status == 404:
        return "unavailable", []
    if status >= 400:
        return "unavailable", []
    items = payload.get("items") if isinstance(payload, dict) else None
    comments: list[CommentSnippet] = []
    if isinstance(items, list):
        for item in items[:15]:
            snippet = (
                item.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
                if isinstance(item, dict)
                else {}
            )
            text = str(snippet.get("textDisplay") or snippet.get("textOriginal") or "").strip()
            if text == "":
                continue
            likes = _optional_count(snippet.get("likeCount"))
            comments.append(
                CommentSnippet(
                    author=str(snippet.get("authorDisplayName") or "Viewer")[:80],
                    text=text[:500],
                    like_count=likes,
                )
            )
    return "available", comments


def transcript_status() -> TranscriptStatus:
    return TranscriptStatus(available=False, text="", reason=TRANSCRIPT_REASON)


def analytics_status() -> AnalyticsAvailability:
    return AnalyticsAvailability(
        connected=False,
        impressions=None,
        click_through_rate=None,
        audience_retention=None,
        reason=ANALYTICS_REASON,
    )


def default_fetcher(url: str, params: dict[str, str]) -> tuple[int, dict[str, Any]]:
    query = dict(params)
    query["key"] = settings.youtube_api_key
    try:
        response = httpx.get(url, params=query, timeout=20.0)
    except httpx.TimeoutException as exc:
        raise YoutubeApiError(504, "The YouTube Data API timed out. No statistics were saved.") from exc
    except httpx.HTTPError as exc:
        raise YoutubeApiError(502, "The YouTube Data API request failed. No statistics were saved.") from exc
    try:
        payload = response.json()
    except ValueError:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}
    return response.status_code, payload


def _request(url: str, params: dict[str, str], fetcher: Fetcher | None) -> tuple[int, dict[str, Any]]:
    call = fetcher or default_fetcher
    return call(url, params)


def _raise_for_api_status(status: int, payload: dict[str, Any]) -> None:
    if status < 400:
        return
    reason = _error_reason(payload)
    if reason in {"quotaExceeded", "dailyLimitExceeded", "rateLimitExceeded"}:
        raise YoutubeApiError(429, "The YouTube Data API quota was reached. No new statistics were retrieved.")
    if status == 400 and reason == "keyInvalid":
        raise YoutubeApiError(502, "YouTube rejected the server API key. No statistics were retrieved.")
    if status in {403, 404}:
        raise YoutubeApiError(404, "YouTube did not return that video. It may be private, deleted, or unavailable.")
    raise YoutubeApiError(502, "The YouTube Data API request failed. No statistics were saved.")


def _error_reason(payload: dict[str, Any]) -> str:
    error = payload.get("error") if isinstance(payload, dict) else None
    if not isinstance(error, dict):
        return ""
    errors = error.get("errors")
    if isinstance(errors, list) and errors and isinstance(errors[0], dict):
        return str(errors[0].get("reason") or "")
    return ""


def _metadata(video_id: str, item: dict[str, Any]) -> VideoMetadata:
    snippet = item.get("snippet") if isinstance(item.get("snippet"), dict) else {}
    thumbnails = snippet.get("thumbnails") if isinstance(snippet.get("thumbnails"), dict) else {}
    thumbnail = ""
    for name in ("high", "medium", "default"):
        candidate = thumbnails.get(name)
        if isinstance(candidate, dict) and candidate.get("url"):
            thumbnail = str(candidate["url"])
            break
    details = item.get("contentDetails") if isinstance(item.get("contentDetails"), dict) else {}
    status = item.get("status") if isinstance(item.get("status"), dict) else {}
    return VideoMetadata(
        video_id=video_id,
        url=canonical_watch_url(video_id),
        title=str(snippet.get("title") or "Untitled video")[:300],
        description=str(snippet.get("description") or "")[:5000],
        channel_title=str(snippet.get("channelTitle") or "Unknown channel")[:200],
        thumbnail_url=thumbnail or None,
        published_at=str(snippet.get("publishedAt") or "") or None,
        duration_seconds=_duration_seconds(str(details.get("duration") or "")),
        privacy_status=str(status.get("privacyStatus") or "public"),
    )


def _statistics(raw: dict[str, Any]) -> PublicStatistics:
    views = _optional_count(raw.get("viewCount")) if "viewCount" in raw else None
    likes = _optional_count(raw.get("likeCount")) if "likeCount" in raw else None
    comments = _optional_count(raw.get("commentCount")) if "commentCount" in raw else None
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


def _optional_count(value: object) -> int | None:
    if value is None or value == "":
        return None
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    if number < 0:
        return None
    return number


def _duration_seconds(value: str) -> int | None:
    match = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", value)
    if match is None or value == "PT":
        return None
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    total = hours * 3600 + minutes * 60 + seconds
    return total if total > 0 else 0
