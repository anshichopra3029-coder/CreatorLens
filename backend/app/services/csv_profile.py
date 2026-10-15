"""Calculate CSV statistics in Python.

These numbers are the source of truth for charts and summaries. A language
model may explain them later, but it does not produce them.
"""

from __future__ import annotations

import math

import pandas as pd

from app.core.metrics import METRIC_FORMULA, METRIC_NAME, METRIC_NOTE, engagement_rate
from app.schemas.documents import AnomalyStat, CategoryStat, ColumnProfile, CsvProfile, TrendStat

ENGAGEMENT_COLUMNS = ("views", "likes", "comments", "shares")
SAMPLE_ROWS = 5
ANOMALY_LIMIT = 8


def _finite(value: float | None) -> float | None:
    if value is None or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        return None
    return round(float(value), 2)


def _optional_number(value: object) -> float | None:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    text = str(value).strip()
    if text == "":
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    if not math.isfinite(number):
        return None
    return number


def profile_csv(frame: pd.DataFrame) -> CsvProfile:
    working = frame.fillna("").astype(str)
    working.columns = [str(column).strip() for column in working.columns]
    columns = [_column_profile(working, name) for name in working.columns]
    sample = _sample_rows(working)
    engagement = _engagement(working)
    anomalies = _anomalies(working, columns)
    return CsvProfile(
        row_count=int(len(working)),
        column_count=int(len(working.columns)),
        columns=columns,
        anomalies=anomalies,
        sample_rows=sample,
        **engagement,
    )


def _column_profile(frame: pd.DataFrame, name: str) -> ColumnProfile:
    series = frame[name]
    missing = int(series.str.strip().eq("").sum())
    present = series[series.str.strip() != ""]
    non_empty = int(len(present))
    numbers = pd.to_numeric(present, errors="coerce")
    try:
        dates = pd.to_datetime(present, errors="coerce", format="mixed")
    except (ValueError, TypeError):
        dates = pd.to_datetime(present, errors="coerce")
    numeric_ratio = float(numbers.notna().mean()) if non_empty else 0.0
    date_ratio = float(dates.notna().mean()) if non_empty else 0.0
    if non_empty and date_ratio >= 0.8 and numeric_ratio < 0.8:
        kind = "datetime"
    elif non_empty and numeric_ratio >= 0.8:
        kind = "number"
    else:
        kind = "text"
    valid_numbers = numbers.dropna()
    return ColumnProfile(
        name=name,
        kind=kind,
        non_empty_count=non_empty,
        missing_count=missing,
        numeric_min=_finite(float(valid_numbers.min())) if kind == "number" and len(valid_numbers) else None,
        numeric_max=_finite(float(valid_numbers.max())) if kind == "number" and len(valid_numbers) else None,
        numeric_mean=_finite(float(valid_numbers.mean())) if kind == "number" and len(valid_numbers) else None,
        numeric_median=_finite(float(valid_numbers.median())) if kind == "number" and len(valid_numbers) else None,
    )


def _sample_rows(frame: pd.DataFrame) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for record in frame.head(SAMPLE_ROWS).to_dict(orient="records"):
        rows.append({str(key): str(value)[:80] for key, value in record.items()})
    return rows


def _engagement(frame: pd.DataFrame) -> dict[str, object]:
    empty: dict[str, object] = {
        "engagement_available": False,
        "metric_name": None,
        "metric_formula": None,
        "metric_note": None,
        "posts_analyzed": None,
        "avg_engagement_rate": None,
        "total_interactions": None,
        "best_category": None,
        "categories": [],
        "trends": [],
    }
    if any(column not in frame.columns for column in ENGAGEMENT_COLUMNS):
        return empty
    rates: list[float] = []
    interactions: list[int] = []
    categories: list[str] = []
    timestamps: list[pd.Timestamp | None] = []
    date_column = "post_datetime" if "post_datetime" in frame.columns else None
    category_column = "category" if "category" in frame.columns else None
    for _, row in frame.iterrows():
        views = _optional_number(row["views"])
        likes = _optional_number(row["likes"])
        comments = _optional_number(row["comments"])
        shares = _optional_number(row["shares"])
        rate = engagement_rate(likes, comments, shares, views)
        if likes is None or comments is None or shares is None:
            interaction = None
        else:
            interaction = int(likes + comments + shares)
        rates.append(rate if rate is not None else math.nan)
        interactions.append(interaction if interaction is not None else 0)
        categories.append(str(row[category_column]).strip() if category_column else "")
        if date_column:
            parsed = pd.to_datetime(row[date_column], errors="coerce")
            timestamps.append(None if pd.isna(parsed) else parsed)
        else:
            timestamps.append(None)
    usable = [rate for rate in rates if not math.isnan(rate)]
    known_interactions = [
        interactions[index]
        for index, rate in enumerate(rates)
        if not math.isnan(rate)
    ]
    category_stats = _category_stats(categories, rates, interactions)
    best = None
    ranked = [item for item in category_stats if item.avg_engagement_rate is not None]
    if ranked:
        best = max(ranked, key=lambda item: item.avg_engagement_rate or 0).name
    return {
        "engagement_available": True,
        "metric_name": METRIC_NAME,
        "metric_formula": METRIC_FORMULA,
        "metric_note": METRIC_NOTE,
        "posts_analyzed": len(usable),
        "avg_engagement_rate": _finite(sum(usable) / len(usable)) if usable else None,
        "total_interactions": int(sum(known_interactions)),
        "best_category": best,
        "categories": category_stats,
        "trends": _trend_stats(timestamps, rates, interactions),
    }


def _category_stats(names: list[str], rates: list[float], interactions: list[int]) -> list[CategoryStat]:
    grouped: dict[str, list[int]] = {}
    for index, name in enumerate(names):
        if name == "":
            continue
        grouped.setdefault(name, []).append(index)
    stats: list[CategoryStat] = []
    for name, indexes in grouped.items():
        usable = [rates[index] for index in indexes if not math.isnan(rates[index])]
        total = sum(interactions[index] for index in indexes if not math.isnan(rates[index]))
        stats.append(
            CategoryStat(
                name=name,
                count=len(indexes),
                avg_engagement_rate=_finite(sum(usable) / len(usable)) if usable else None,
                total_interactions=int(total),
            )
        )
    stats.sort(key=lambda item: (-(item.avg_engagement_rate or -1), item.name))
    return stats


def _trend_stats(
    timestamps: list[pd.Timestamp | None],
    rates: list[float],
    interactions: list[int],
) -> list[TrendStat]:
    if not any(item is not None for item in timestamps):
        return []
    grouped: dict[pd.Period, list[int]] = {}
    for index, stamp in enumerate(timestamps):
        if stamp is None:
            continue
        period = stamp.to_period("W-SUN")
        grouped.setdefault(period, []).append(index)
    trends: list[TrendStat] = []
    for period in sorted(grouped):
        indexes = grouped[period]
        usable = [rates[index] for index in indexes if not math.isnan(rates[index])]
        total = sum(interactions[index] for index in indexes if not math.isnan(rates[index]))
        start = period.start_time.date().isoformat()
        trends.append(
            TrendStat(
                period=start,
                label=start,
                count=len(indexes),
                avg_engagement_rate=_finite(sum(usable) / len(usable)) if usable else None,
                total_interactions=int(total),
            )
        )
    return trends


def _anomalies(frame: pd.DataFrame, columns: list[ColumnProfile]) -> list[AnomalyStat]:
    found: list[AnomalyStat] = []
    for column in columns:
        if column.kind != "number":
            continue
        numbers = pd.to_numeric(frame[column.name], errors="coerce")
        valid = numbers.dropna()
        if len(valid) < 4:
            continue
        q1 = float(valid.quantile(0.25))
        q3 = float(valid.quantile(0.75))
        spread = q3 - q1
        if spread == 0:
            continue
        low = q1 - 1.5 * spread
        high = q3 + 1.5 * spread
        for index, value in numbers.items():
            if pd.isna(value) or (low <= float(value) <= high):
                continue
            found.append(
                AnomalyStat(
                    row_number=int(index) + 1,
                    column=column.name,
                    value=_finite(float(value)) or 0,
                    reason=f"Outside the typical range of {round(low, 2)} to {round(high, 2)}.",
                )
            )
            if len(found) >= ANOMALY_LIMIT:
                return found
    return found
