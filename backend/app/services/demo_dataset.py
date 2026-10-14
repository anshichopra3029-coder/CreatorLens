"""Load the built-in demo posts and calculate dashboard figures from them.

Every number returned by the demo endpoints comes from
``app/data/demo_posts.csv`` and the shared engagement-rate function.
Nothing here reads an uploaded file.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path

import pandas as pd

from app.core.metrics import METRIC_FORMULA, METRIC_NAME, METRIC_NOTE, engagement_rate

DEMO_CSV = Path(__file__).resolve().parents[1] / "data" / "demo_posts.csv"
REQUIRED_COLUMNS = (
    "post_id",
    "platform",
    "category",
    "post_datetime",
    "views",
    "likes",
    "comments",
    "shares",
    "followers_gained",
    "title",
)


@dataclass(frozen=True)
class DemoQuery:
    category: str | None = None
    platform: str | None = None
    start_date: date | None = None
    end_date: date | None = None

    def applied_filters(self) -> dict[str, str | None]:
        return {
            "category": self.category,
            "platform": self.platform,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
        }


def _metric_fields() -> dict[str, object]:
    return {
        "is_demo": True,
        "data_source": "demo",
        "metric_name": METRIC_NAME,
        "metric_formula": METRIC_FORMULA,
    }


def _average(values: pd.Series) -> float | None:
    numeric = pd.to_numeric(values, errors="coerce").dropna()
    if numeric.empty:
        return None
    mean = float(numeric.mean())
    if not math.isfinite(mean):
        return None
    return round(mean, 2)


def _average_int(values: pd.Series) -> int | None:
    numeric = pd.to_numeric(values, errors="coerce").dropna()
    if numeric.empty:
        return None
    mean = float(numeric.mean())
    if not math.isfinite(mean):
        return None
    return int(round(mean))


def _interactions(frame: pd.DataFrame) -> int:
    if frame.empty:
        return 0
    total = float((frame["likes"] + frame["comments"] + frame["shares"]).sum())
    if not math.isfinite(total):
        return 0
    return int(total)


def group_metrics(frame: pd.DataFrame, column: str) -> list[dict[str, object]]:
    if frame.empty:
        return []
    rows: list[dict[str, object]] = []
    for name, group in frame.groupby(column, sort=False):
        rows.append(
            {
                "name": str(name),
                "post_count": int(len(group)),
                "avg_engagement_rate": _average(group["engagement_rate"]),
                "total_interactions": _interactions(group),
                "avg_views": _average_int(group["views"]),
            }
        )
    rows.sort(
        key=lambda row: (
            -(float(row["avg_engagement_rate"]) if row["avg_engagement_rate"] is not None else -1),
            str(row["name"]),
        )
    )
    return rows


@lru_cache(maxsize=1)
def _load_demo_frame() -> pd.DataFrame:
    frame = pd.read_csv(DEMO_CSV)
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise RuntimeError(f"Demo dataset is missing columns: {', '.join(missing)}")

    frame["post_datetime"] = pd.to_datetime(frame["post_datetime"], errors="raise")
    for column in ("views", "likes", "comments", "shares", "followers_gained"):
        frame[column] = pd.to_numeric(frame[column], errors="raise")

    frame["engagement_rate"] = [
        engagement_rate(float(likes), float(comments), float(shares), float(views))
        for likes, comments, shares, views in zip(
            frame["likes"],
            frame["comments"],
            frame["shares"],
            frame["views"],
            strict=True,
        )
    ]
    return frame


def select_demo_posts(query: DemoQuery | None = None) -> pd.DataFrame:
    """Return a copy of the demo posts, optionally narrowed by the query."""
    frame = _load_demo_frame().copy()
    selected = query or DemoQuery()
    if selected.category:
        frame = frame.loc[frame["category"] == selected.category]
    if selected.platform:
        frame = frame.loc[frame["platform"] == selected.platform]
    if selected.start_date:
        frame = frame.loc[frame["post_datetime"] >= pd.Timestamp(selected.start_date)]
    if selected.end_date:
        frame = frame.loc[frame["post_datetime"] <= pd.Timestamp(selected.end_date)]
    return frame.copy()


def build_summary(query: DemoQuery) -> dict[str, object]:
    frame = select_demo_posts(query)
    categories = group_metrics(frame, "category")
    best_category = str(categories[0]["name"]) if categories else None
    return {
        **_metric_fields(),
        "metric_note": METRIC_NOTE,
        "posts_analyzed": int(len(frame)),
        "avg_engagement_rate": _average(frame["engagement_rate"]) if not frame.empty else None,
        "total_interactions": _interactions(frame),
        "best_category": best_category,
        "applied_filters": query.applied_filters(),
    }


def build_trends(query: DemoQuery) -> dict[str, object]:
    frame = select_demo_posts(query)
    points: list[dict[str, object]] = []
    if not frame.empty:
        working = frame.copy()
        working["week_start"] = working["post_datetime"].dt.to_period("W-SUN").dt.start_time
        for week, group in working.groupby("week_start", sort=True):
            start = pd.Timestamp(week)
            points.append(
                {
                    "period": start.date().isoformat(),
                    "label": f"{start.day} {start.strftime('%b')}",
                    "avg_engagement_rate": _average(group["engagement_rate"]),
                    "post_count": int(len(group)),
                    "total_interactions": _interactions(group),
                }
            )
    return {
        **_metric_fields(),
        "points": points,
        "applied_filters": query.applied_filters(),
    }


def build_comparison(query: DemoQuery) -> dict[str, object]:
    frame = select_demo_posts(query)
    return {
        **_metric_fields(),
        "categories": group_metrics(frame, "category"),
        "platforms": group_metrics(frame, "platform"),
        "applied_filters": query.applied_filters(),
    }


def _json_rate(value: object) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def build_posts(query: DemoQuery) -> dict[str, object]:
    frame = select_demo_posts(query)
    ordered = frame.sort_values(["post_datetime", "post_id"], ascending=[False, True])
    posts: list[dict[str, object]] = []
    for row in ordered.itertuples(index=False):
        posted = pd.Timestamp(row.post_datetime).date().isoformat()
        posts.append(
            {
                "post_id": str(row.post_id),
                "title": str(row.title),
                "platform": str(row.platform),
                "category": str(row.category),
                "post_datetime": posted,
                "views": int(row.views),
                "likes": int(row.likes),
                "comments": int(row.comments),
                "shares": int(row.shares),
                "followers_gained": int(row.followers_gained),
                "engagement_rate": _json_rate(row.engagement_rate),
            }
        )
    return {
        **_metric_fields(),
        "count": len(posts),
        "posts": posts,
        "applied_filters": query.applied_filters(),
    }
