"""Validate a creator analytics CSV and map it to one internal schema.

Missing numbers stay missing. Duplicate video-and-date rows stop the import
instead of being dropped.
"""

from __future__ import annotations

import io
import re
from datetime import datetime

import pandas as pd
from pydantic import BaseModel, Field

CANONICAL = (
    "video_id",
    "title",
    "observed_at",
    "views",
    "likes",
    "comments",
    "shares",
    "impressions",
    "click_through_rate",
    "watch_time_minutes",
    "average_view_duration_seconds",
    "subscribers_gained",
)
ALIASES = {
    "video_id": "video_id",
    "videoid": "video_id",
    "id": "video_id",
    "title": "title",
    "video_title": "title",
    "name": "title",
    "date": "observed_at",
    "timestamp": "observed_at",
    "observed_at": "observed_at",
    "day": "observed_at",
    "views": "views",
    "view_count": "views",
    "view": "views",
    "likes": "likes",
    "like_count": "likes",
    "like": "likes",
    "comments": "comments",
    "comment_count": "comments",
    "comment": "comments",
    "shares": "shares",
    "share_count": "shares",
    "share": "shares",
    "impressions": "impressions",
    "impression": "impressions",
    "ctr": "click_through_rate",
    "click_through_rate": "click_through_rate",
    "click_through": "click_through_rate",
    "watch_time": "watch_time_minutes",
    "watch_time_minutes": "watch_time_minutes",
    "average_view_duration": "average_view_duration_seconds",
    "average_view_duration_seconds": "average_view_duration_seconds",
    "avg_view_duration": "average_view_duration_seconds",
    "subscribers_gained": "subscribers_gained",
    "subscribers": "subscribers_gained",
}
COUNT_FIELDS = (
    "views",
    "likes",
    "comments",
    "shares",
    "impressions",
    "watch_time_minutes",
    "average_view_duration_seconds",
    "subscribers_gained",
)
RATE_FIELDS = ("click_through_rate",)


class AnalyticsCsvError(Exception):
    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


class AnalyticsObservation(BaseModel):
    video_id: str
    title: str
    observed_at: str | None = None
    views: int | None = None
    likes: int | None = None
    comments: int | None = None
    shares: int | None = None
    impressions: int | None = None
    click_through_rate: float | None = None
    watch_time_minutes: float | None = None
    average_view_duration_seconds: float | None = None
    subscribers_gained: int | None = None


class ParsedAnalytics(BaseModel):
    filename: str
    columns: list[str]
    observations: list[AnalyticsObservation]
    warnings: list[str] = Field(default_factory=list)
    has_shares: bool = False
    preview: list[AnalyticsObservation] = Field(default_factory=list)


def parse_analytics_csv(raw: bytes, filename: str, *, max_rows: int) -> ParsedAnalytics:
    if not filename.lower().endswith(".csv"):
        raise AnalyticsCsvError("Upload a .csv file. PDF and DOCX files stay on the document analysis page.")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise AnalyticsCsvError("The CSV must be UTF-8 text.") from exc
    if text.strip() == "":
        raise AnalyticsCsvError("The CSV is empty.")
    try:
        frame = pd.read_csv(io.StringIO(text), dtype=str, keep_default_na=False)
    except pd.errors.ParserError as exc:
        raise AnalyticsCsvError("The CSV could not be read. Check that quotes and columns are valid.") from exc
    if frame.empty or len(frame.columns) == 0:
        raise AnalyticsCsvError("The CSV has no rows.")
    if len(frame.index) > max_rows:
        raise AnalyticsCsvError(f"The CSV has more than {max_rows} rows.")
    mapping, warnings = _map_columns(list(frame.columns))
    observations: list[AnalyticsObservation] = []
    errors: list[str] = []
    seen: set[tuple[str, str]] = set()
    for row_number, row in enumerate(frame.to_dict(orient="records"), start=2):
        try:
            observation = _row(row, mapping)
        except AnalyticsCsvError as exc:
            errors.append(f"Row {row_number}: {exc.detail}")
            if len(errors) >= 8:
                break
            continue
        if observation.observed_at:
            key = (observation.video_id, observation.observed_at)
            if key in seen:
                errors.append(
                    f"Row {row_number}: {observation.video_id} is already recorded on {observation.observed_at}."
                )
            seen.add(key)
        observations.append(observation)
    if errors:
        raise AnalyticsCsvError(" ".join(errors))
    if not observations:
        raise AnalyticsCsvError("The CSV has no usable rows.")
    return ParsedAnalytics(
        filename=_safe_filename(filename),
        columns=sorted(set(mapping.values())),
        observations=observations,
        warnings=warnings,
        has_shares="shares" in mapping.values(),
        preview=observations[:8],
    )


def _map_columns(columns: list[str]) -> tuple[dict[str, str], list[str]]:
    mapping: dict[str, str] = {}
    used: dict[str, str] = {}
    unknown: list[str] = []
    for original in columns:
        key = re.sub(r"[^a-z0-9]+", "_", original.strip().lower()).strip("_")
        canonical = ALIASES.get(key)
        if canonical is None:
            unknown.append(original)
            continue
        if canonical in used:
            raise AnalyticsCsvError(
                f"The columns {used[canonical]} and {original} both describe {canonical}. Keep one of them."
            )
        mapping[original] = canonical
        used[canonical] = original
    if "video_id" not in used and "title" not in used:
        raise AnalyticsCsvError("The CSV needs a video ID column or a video title column.")
    if not any(name in used for name in ("views", "likes", "comments")):
        raise AnalyticsCsvError("The CSV needs a views, likes, or comments column.")
    warnings = []
    if unknown:
        warnings.append("These columns were kept out of the analysis: " + ", ".join(unknown) + ".")
    return mapping, warnings


def _row(row: dict[str, str], mapping: dict[str, str]) -> AnalyticsObservation:
    values = {canonical: str(row.get(original, "")).strip() for original, canonical in mapping.items()}
    title = values.get("title") or "Untitled video"
    video_id = values.get("video_id") or _title_key(title)
    if video_id == "":
        raise AnalyticsCsvError("A video ID or title is required.")
    observed = _date(values.get("observed_at", ""))
    payload: dict[str, object] = {"video_id": video_id[:80], "title": title[:300], "observed_at": observed}
    for field in COUNT_FIELDS:
        payload[field] = _count(values.get(field, ""), field)
    payload["click_through_rate"] = _rate(values.get("click_through_rate", ""))
    observation = AnalyticsObservation.model_validate(payload)
    if observation.views is None and observation.likes is None and observation.comments is None:
        raise AnalyticsCsvError("Views, likes, and comments are all missing.")
    return observation


def _date(value: str) -> str | None:
    if value == "":
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text).date().isoformat()
    except ValueError as exc:
        raise AnalyticsCsvError(f"{value} is not a supported date. Use YYYY-MM-DD.") from exc


def _count(value: str, field: str) -> int | float | None:
    if value == "":
        return None
    try:
        number = float(value.replace(",", ""))
    except ValueError as exc:
        raise AnalyticsCsvError(f"{field} must be a number.") from exc
    if number < 0:
        raise AnalyticsCsvError(f"{field} cannot be negative.")
    if field in {"watch_time_minutes", "average_view_duration_seconds"}:
        return round(number, 4)
    if not number.is_integer():
        raise AnalyticsCsvError(f"{field} must be a whole number.")
    return int(number)


def _rate(value: str) -> float | None:
    if value == "":
        return None
    text = value.strip()
    percent = text.endswith("%")
    if percent:
        text = text[:-1]
    try:
        number = float(text.replace(",", ""))
    except ValueError as exc:
        raise AnalyticsCsvError("click_through_rate must be a number.") from exc
    if percent:
        number = number / 100
    if number > 1:
        raise AnalyticsCsvError("click_through_rate must be a fraction such as 0.05, or a percent such as 5%.")
    if number < 0:
        raise AnalyticsCsvError("click_through_rate cannot be negative.")
    return round(number, 6)


def _title_key(title: str) -> str:
    key = re.sub(r"[^a-z0-9]+", "-", title.strip().lower()).strip("-")
    return key[:80] or "untitled"


def _safe_filename(filename: str) -> str:
    base = filename.replace("\\", "/").split("/")[-1]
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", base)[:120]
    return cleaned or "upload.csv"

