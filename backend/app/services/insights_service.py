"""Build short demo insights from the same figures as the dashboard.

The wording describes the sample and states that it is not a causal finding.
Uploads are not an input to this service in Phase 1.
"""

from __future__ import annotations

import math

import pandas as pd

from app.core.metrics import METRIC_FORMULA, METRIC_NAME
from app.services.demo_dataset import DemoQuery, group_metrics, select_demo_posts

DISCLAIMER = (
    "These cards are calculated from the built-in demo dataset so the interface "
    "can be reviewed before a real analysis pipeline exists. They are illustrative, "
    "they are not causal findings, and they do not describe a file you upload in this phase."
)


def _format_rate(value: object) -> str:
    if value is None:
        return "unavailable"
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return "unavailable"
    if not math.isfinite(number):
        return "unavailable"
    return f"{number:.2f}%"


def _finite(value: object) -> float | None:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def build_insights() -> dict[str, object]:
    frame = select_demo_posts(DemoQuery())
    cards: list[dict[str, str]] = []

    categories = group_metrics(frame, "category")
    if categories:
        best = categories[0]
        lowest = categories[-1]
        if best["name"] == lowest["name"]:
            spread = f"Only {best['name']} is present, across {best['post_count']} posts."
        else:
            spread = (
                f"{lowest['name']} is the lowest at {_format_rate(lowest['avg_engagement_rate'])} "
                f"across {lowest['post_count']} posts."
            )
        cards.append(
            {
                "id": "category-comparison",
                "title": "Category comparison",
                "summary": (
                    f"In the demo dataset, {best['name']} has the highest average "
                    f"view-based engagement rate at {_format_rate(best['avg_engagement_rate'])} "
                    f"across {best['post_count']} posts."
                ),
                "evidence": (
                    f"{best['name']}: {best['post_count']} posts, average rate "
                    f"{_format_rate(best['avg_engagement_rate'])}, "
                    f"{best['total_interactions']} interactions. {spread} "
                    f"The rate is {METRIC_FORMULA}. "
                    "This describes the sample. It is not evidence that the category caused the result."
                ),
            }
        )

    platforms = group_metrics(frame, "platform")
    if platforms:
        leading = platforms[0]
        cards.append(
            {
                "id": "engagement-patterns",
                "title": "Engagement patterns",
                "summary": (
                    f"Among the demo platforms, {leading['name']} has the highest average "
                    f"view-based engagement rate at {_format_rate(leading['avg_engagement_rate'])}."
                ),
                "evidence": (
                    f"{leading['name']} accounts for {leading['post_count']} demo posts and "
                    f"{leading['total_interactions']} interactions (likes + comments + shares). "
                    "A higher rate on one platform in this small sample is not evidence that "
                    "the platform caused better performance."
                ),
            }
        )

    rated = frame.copy()
    rated["rate_value"] = rated["engagement_rate"].map(_finite)
    rated = rated.dropna(subset=["rate_value"])
    if not rated.empty:
        highest = rated.sort_values(["rate_value", "post_datetime"], ascending=[False, False]).iloc[0]
        lowest_post = rated.sort_values(["rate_value", "post_datetime"], ascending=[True, True]).iloc[0]
        cards.append(
            {
                "id": "high-low-posts",
                "title": "High and low performing posts",
                "summary": (
                    f"The highest demo rate is {_format_rate(highest['rate_value'])} "
                    f"for “{highest['title']}”. The lowest is {_format_rate(lowest_post['rate_value'])} "
                    f"for “{lowest_post['title']}”."
                ),
                "evidence": (
                    f"Highest: {highest['post_id']}, {highest['platform']}, {highest['category']}, "
                    f"{int(highest['views'])} views, rate {_format_rate(highest['rate_value'])}. "
                    f"Lowest: {lowest_post['post_id']}, {lowest_post['platform']}, {lowest_post['category']}, "
                    f"{int(lowest_post['views'])} views, rate {_format_rate(lowest_post['rate_value'])}. "
                    "Both rates use the same view-based formula. A single post is not a rule for what to publish next."
                ),
            }
        )

    if not frame.empty:
        start = pd.Timestamp(frame["post_datetime"].min())
        end = pd.Timestamp(frame["post_datetime"].max())
        midpoint = start + (end - start) / 2
        earlier = frame.loc[frame["post_datetime"] <= midpoint]
        later = frame.loc[frame["post_datetime"] > midpoint]
        earlier_rate = _format_rate(None if earlier.empty else _mean_rate(earlier))
        later_rate = _format_rate(None if later.empty else _mean_rate(later))
        cards.append(
            {
                "id": "possible-trends",
                "title": "Possible trends",
                "summary": (
                    f"Earlier demo posts average {earlier_rate}. Later demo posts average {later_rate}."
                ),
                "evidence": (
                    f"The timeline runs from {start.date().isoformat()} to {end.date().isoformat()}. "
                    f"The split point is {midpoint.date().isoformat()}. "
                    f"Earlier side: {len(earlier)} posts at {earlier_rate}. "
                    f"Later side: {len(later)} posts at {later_rate}. "
                    "This is a description of the demo timeline, not a forecast, and it does not "
                    "show that time caused the change."
                ),
            }
        )

    return {
        "is_demo": True,
        "data_source": "demo",
        "disclaimer": DISCLAIMER,
        "metric_name": METRIC_NAME,
        "metric_formula": METRIC_FORMULA,
        "cards": cards,
    }


def _mean_rate(frame: pd.DataFrame) -> float | None:
    values = [number for number in (_finite(value) for value in frame["engagement_rate"]) if number is not None]
    if not values:
        return None
    return round(sum(values) / len(values), 2)
