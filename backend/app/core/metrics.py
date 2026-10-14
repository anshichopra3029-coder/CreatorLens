"""The one engagement-rate definition used by CreatorLens.

view_based_engagement_rate = (likes + comments + shares) / views * 100

A missing component stays missing. A real zero stays zero. A missing or
non-positive view count cannot be a denominator, so the rate is unavailable
instead of becoming infinity or NaN.
"""

from __future__ import annotations

import math

METRIC_NAME = "view_based_engagement_rate"
METRIC_FORMULA = "(likes + comments + shares) / views * 100"
METRIC_NOTE = (
    "The average is the mean of per-post view-based engagement rates. "
    "Posts whose views are missing or not positive are left out of that average. "
    "Likes, comments, and shares are not filled in when they are missing."
)


def engagement_rate(
    likes: float | None,
    comments: float | None,
    shares: float | None,
    views: float | None,
) -> float | None:
    """Return the view-based engagement rate rounded to two decimals."""
    if likes is None or comments is None or shares is None or views is None:
        return None
    if not all(math.isfinite(value) for value in (likes, comments, shares, views)):
        return None
    if views <= 0:
        return None
    rate = (likes + comments + shares) / views * 100
    if not math.isfinite(rate):
        return None
    return round(rate, 2)
