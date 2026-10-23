"""Dated view history for one YouTube video: import, collection, and forecast.

Observations come from three places, all with a real timestamp:

* saved analyses (each fresh metadata fetch is a snapshot),
* ``POST /api/youtube/videos/{id}/snapshot`` or the collector below, which fetch
  the current public count without the metadata cache,
* a creator's CSV import.

CSV format (UTF-8, header row required)::

    observed_at,views
    2026-10-01T09:00:00Z,1200
    2026-10-02T09:00:00Z,1850
    2026-10-03,2400

* ``observed_at`` (also ``timestamp``, ``date``, ``datetime``): ISO 8601. A date
  alone means 00:00 UTC. A time without a zone is read as UTC. Future times are
  rejected.
* ``views`` (also ``view_count``): a whole number of at least 0. Commas are allowed.
* ``video_id`` is optional. When present, every row must match the video in the URL.
* The same timestamp may not appear twice in one file. A timestamp that is
  already stored for this video is skipped, not overwritten.

Collect snapshots for every saved video from ``backend`` (for example from
Windows Task Scheduler every few hours)::

    python -m app.services.view_history --collect
"""

from __future__ import annotations

import argparse
import csv
import io
from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.schemas.prediction import (
    ObservationImportResult,
    TrackedVideo,
    VideoForecastResponse,
    ViewObservation,
)
from app.services.prediction import (
    MIN_EVALUATION_POINTS,
    MIN_FORECAST_POINTS,
    clean_observations,
    forecast_from_history,
    parse_timestamp,
    with_recorded_history,
)
from app.services.youtube_client import YoutubeApiError, fetch_video
from app.services.youtube_store import (
    analyses_for_video,
    insert_observations,
    observation_points,
    put_cached_video,
    stored_observations,
    tracked_videos,
)
from app.services.youtube_urls import _valid_video_id

MIN_SNAPSHOT_GAP = timedelta(hours=1)
TIME_COLUMNS = ("observed_at", "timestamp", "date", "datetime", "observed")
VIEW_COLUMNS = ("views", "view_count", "viewcount")


class ViewHistoryError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def list_tracked(user_id: str) -> list[TrackedVideo]:
    return [TrackedVideo.model_validate(item) for item in tracked_videos(user_id)]


def video_forecast(video_id: str, user_id: str) -> VideoForecastResponse:
    records = _require_video(video_id, user_id)
    latest = records[-1]
    points = observation_points(video_id, user_id)
    pairs = [(stamp, views) for stamp, views, _ in points]
    prediction, _ = forecast_from_history(pairs)
    prediction = with_recorded_history(prediction, clean_observations(pairs)[0])
    distinct = len({stamp for stamp, _, _ in points})
    if distinct < MIN_FORECAST_POINTS:
        guidance = (
            f"{distinct} view count(s) saved so far. Record another snapshot after at least an hour, or import dated "
            f"history from a CSV file. A forecast appears once there are {MIN_FORECAST_POINTS} counts. From "
            f"{MIN_EVALUATION_POINTS} counts, we also test which forecast method is more accurate."
        )
    elif distinct < MIN_EVALUATION_POINTS:
        guidance = (
            f"{distinct} view counts saved. The forecast is still an early one until there are {MIN_EVALUATION_POINTS} "
            "counts to test it against."
        )
    else:
        guidance = "Keep recording snapshots regularly so we can keep checking the forecast against your real view counts."
    return VideoForecastResponse(
        video_id=video_id,
        title=latest.metadata.title,
        channel_title=latest.metadata.channel_title,
        latest_analysis_id=latest.id,
        observations=[ViewObservation(observed_at=stamp, views=views, source=source) for stamp, views, source in points],  # type: ignore[arg-type]
        prediction=prediction,
        guidance=guidance,
    )


def record_snapshot(video_id: str, user_id: str, *, extractor=None, now: datetime | None = None) -> VideoForecastResponse:
    _require_video(video_id, user_id)
    current = (now or datetime.now(timezone.utc)).replace(microsecond=0)
    points = observation_points(video_id, user_id)
    if points:
        last = parse_timestamp(points[-1][0])
        if last is not None and current - last < MIN_SNAPSHOT_GAP:
            wait = int((MIN_SNAPSHOT_GAP - (current - last)).total_seconds() // 60) + 1
            raise ViewHistoryError(
                429,
                f"A view count was already recorded at {points[-1][0]}. Please wait about {wait} minute(s) before the next "
                "snapshot, so it shows a real change instead of a repeat.",
            )
    try:
        metadata, statistics = fetch_video(video_id, extractor=extractor)
    except YoutubeApiError as exc:
        raise ViewHistoryError(exc.status_code, exc.detail) from exc
    if statistics.views is None:
        raise ViewHistoryError(422, "YouTube didn't show a public view count for this video, so nothing was recorded.")
    put_cached_video(
        video_id,
        {"metadata": metadata.model_dump(mode="json"), "statistics": statistics.model_dump(mode="json")},
    )
    insert_observations(user_id, video_id, [(current.isoformat(), statistics.views)], "snapshot")
    return video_forecast(video_id, user_id)


def import_observations(video_id: str, user_id: str, raw: bytes, *, now: datetime | None = None) -> ObservationImportResult:
    _require_video(video_id, user_id)
    rows, notes = parse_history_csv(raw, video_id, now=now)
    inserted, skipped = insert_observations(user_id, video_id, rows, "csv")
    if skipped:
        notes.append(f"{skipped} row(s) were skipped because that date and time was already saved for this video.")
    return ObservationImportResult(
        video_id=video_id,
        rows_read=len(rows),
        inserted=inserted,
        skipped_existing=skipped,
        warnings=notes,
        forecast=video_forecast(video_id, user_id),
    )


def parse_history_csv(raw: bytes, video_id: str, *, now: datetime | None = None) -> tuple[list[tuple[str, int]], list[str]]:
    if not raw.strip():
        raise ViewHistoryError(400, "The file is empty.")
    if len(raw) > settings.max_upload_bytes:
        raise ViewHistoryError(413, f"The file is larger than the {settings.max_upload_size_mb} MB upload limit.")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ViewHistoryError(400, "We couldn't read this CSV's text. Try saving it again as 'CSV UTF-8'.") from exc
    reader = csv.DictReader(io.StringIO(text))
    headers = {(name or "").strip().lower().replace(" ", "_"): name for name in (reader.fieldnames or [])}
    time_key = next((headers[name] for name in TIME_COLUMNS if name in headers), None)
    view_key = next((headers[name] for name in VIEW_COLUMNS if name in headers), None)
    id_key = headers.get("video_id")
    missing = [label for label, key in (("observed_at", time_key), ("views", view_key)) if key is None]
    if missing:
        raise ViewHistoryError(
            422,
            f"Missing column(s): {', '.join(missing)}. The first row should name the columns, like 'observed_at,views'. "
            "If you add a video_id column, it must match this video.",
        )
    current = now or datetime.now(timezone.utc)
    errors: list[str] = []
    seen: dict[str, int] = {}
    rows: list[tuple[str, int]] = []
    for line, row in enumerate(reader, start=2):
        if len(rows) + len(errors) >= settings.max_upload_rows:
            raise ViewHistoryError(400, f"The CSV has more than {settings.max_upload_rows} rows.")
        stamp_text = (row.get(time_key) or "").strip()
        views_text = (row.get(view_key) or "").strip().replace(",", "")
        if id_key is not None and (row.get(id_key) or "").strip() != video_id:
            errors.append(f"Row {line}: video_id '{(row.get(id_key) or '').strip()}' is not {video_id}.")
            continue
        stamp = parse_timestamp(stamp_text)
        if stamp is None:
            errors.append(f"Row {line}: '{stamp_text}' isn't a date we can read. Use a format like 2026-10-01 or 2026-10-01T09:00:00Z.")
            continue
        if stamp > current + timedelta(minutes=5):
            errors.append(f"Row {line}: {stamp.isoformat()} is in the future.")
            continue
        if not views_text.isdigit():
            errors.append(f"Row {line}: views '{views_text}' must be a whole number of at least 0.")
            continue
        key = stamp.replace(microsecond=0).isoformat()
        if key in seen:
            errors.append(f"Row {line}: {key} repeats row {seen[key]}.")
            continue
        seen[key] = line
        rows.append((key, int(views_text)))
    if errors:
        shown = " ".join(errors[:8])
        more = f" {len(errors) - 8} more row(s) also have problems." if len(errors) > 8 else ""
        raise ViewHistoryError(422, f"Nothing was imported. {shown}{more}")
    if not rows:
        raise ViewHistoryError(422, "The CSV has a header but no data rows.")
    rows.sort()
    notes: list[str] = []
    drops = sum(1 for index in range(1, len(rows)) if rows[index][1] < rows[index - 1][1])
    if drops:
        notes.append(f"Views go down {drops} time(s) in this file. We kept the numbers exactly as you supplied them.")
    return rows, notes


def collect_all(user_id: str = "local", *, extractor=None) -> list[str]:
    report: list[str] = []
    for item in tracked_videos(user_id):
        video_id = str(item["video_id"])
        try:
            result = record_snapshot(video_id, user_id, extractor=extractor)
            report.append(f"{video_id}: recorded {result.observations[-1].views:,} views")
        except ViewHistoryError as exc:
            report.append(f"{video_id}: skipped ({exc.detail})")
    return report


def _require_video(video_id: str, user_id: str):
    if not _valid_video_id(video_id):
        raise ViewHistoryError(400, "That isn't a valid YouTube video ID. It should be 11 characters (letters, numbers, '-' or '_').")
    records = analyses_for_video(video_id, user_id)
    if not records and not stored_observations(video_id, user_id):
        raise ViewHistoryError(404, "This video hasn't been saved yet. Analyze it on the Analyze YouTube page first.")
    if not records:
        raise ViewHistoryError(404, "Analyze this video on the Analyze YouTube page first, so we know its title and channel.")
    return records


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Record dated public view counts for saved videos.")
    parser.add_argument("--collect", action="store_true", help="Record a fresh snapshot for every saved video.")
    parser.add_argument("--user-id", default="local")
    args = parser.parse_args(argv)
    if not args.collect:
        parser.print_help()
        return 1
    for line in collect_all(args.user_id):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
