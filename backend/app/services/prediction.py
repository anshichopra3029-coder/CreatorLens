"""Baseline view forecasts from dated observations.

A last-value baseline and a straight-line fit are compared on the latest
observations. The displayed forecast is then refit on every observation.
One public video snapshot is not enough to train either method.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from statistics import median

import numpy as np

from app.schemas.prediction import ForecastPoint, PredictionResult, insufficient_prediction

MODEL_VERSION = "baseline-views-v1"
MIN_POINTS = 8

SINGLE_SNAPSHOT = (
    "This analysis has one public snapshot. A forecast needs at least eight dated view counts "
    "for the same video, from later snapshots or an analytics CSV. No model was trained."
)


def views_per_day(views: int | None, published_at: str | None, now: datetime | None = None) -> float | None:
    """Average public views per day since publication. Not a recent daily trend."""
    if views is None or not published_at:
        return None
    try:
        published = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
    except ValueError:
        return None
    if published.tzinfo is None:
        published = published.replace(tzinfo=timezone.utc)
    current = now or datetime.now(timezone.utc)
    hours = (current - published).total_seconds() / 3600
    if hours < 1:
        return None
    return round(views / (hours / 24), 2)


def forecast_from_history(points: list[tuple[str, int | None]]) -> tuple[PredictionResult, list[str]]:
    """Collapse same-day snapshots to the latest view count, then forecast if eligible."""
    warnings: list[str] = []
    by_day: dict[date, tuple[str, int]] = {}
    collapsed = False
    for created, views in points:
        if views is None:
            continue
        try:
            day = date.fromisoformat(created[:10])
        except ValueError:
            continue
        previous = by_day.get(day)
        if previous is not None and previous[0] != created:
            collapsed = True
        if previous is None or created >= previous[0]:
            by_day[day] = (created, views)
    if collapsed:
        warnings.append(
            "More than one snapshot fell on the same date. The latest view count for that date was used."
        )
    series = [(day, by_day[day][1]) for day in sorted(by_day)]
    if len(series) <= 1:
        message = SINGLE_SNAPSHOT if len(series) == 1 else (
            "No view count was available, so no forecast was trained."
        )
        return insufficient_prediction(message), warnings
    return forecast_views(series), warnings


def forecast_views(observations: list[tuple[date, int]], *, now: datetime | None = None) -> PredictionResult:
    ordered = sorted(observations, key=lambda item: item[0])
    unique: list[tuple[date, int]] = []
    for observed_at, views in ordered:
        if views < 0:
            continue
        if unique and unique[-1][0] == observed_at:
            unique[-1] = (observed_at, views)
        else:
            unique.append((observed_at, views))
    if len(unique) < MIN_POINTS:
        return insufficient_prediction(
            f"Only {len(unique)} dated view observation(s) are available. "
            f"At least {MIN_POINTS} are required before a model is trained."
        )
    gaps = [(unique[index][0] - unique[index - 1][0]).days for index in range(1, len(unique))]
    cadence = float(median(gaps)) if gaps else 1.0
    if cadence < 1:
        cadence = 1.0
    test_count = max(2, len(unique) // 5)
    train = unique[:-test_count]
    test = unique[-test_count:]
    if len(train) < 4:
        return insufficient_prediction("The chronological training split would be shorter than four observations.")

    origin = unique[0][0]
    train_x = np.array([(item[0] - origin).days for item in train], dtype=float)
    train_y = np.array([item[1] for item in train], dtype=float)
    test_x = np.array([(item[0] - origin).days for item in test], dtype=float)
    test_y = np.array([item[1] for item in test], dtype=float)

    slope, intercept = _line(train_x, train_y)
    linear_test = slope * test_x + intercept
    naive_test = np.full(test_y.shape, train_y[-1])
    linear_mae = _mae(test_y, linear_test)
    naive_mae = _mae(test_y, naive_test)
    use_linear = linear_mae < naive_mae
    method = "linear_regression" if use_linear else "naive_last_value"

    all_x = np.array([(item[0] - origin).days for item in unique], dtype=float)
    all_y = np.array([item[1] for item in unique], dtype=float)
    if use_linear:
        slope, intercept = _line(all_x, all_y)
        fitted = slope * all_x + intercept
    else:
        fitted = np.full(all_y.shape, all_y[-1])
    residual_std = float(np.std(all_y - fitted))
    step_days = max(1, int(round(cadence)))
    horizon = 7 if 0.8 <= cadence <= 1.2 else 4
    if 0.8 <= cadence <= 1.2:
        horizon_label = "next 7 days"
    elif 6 <= cadence <= 8:
        horizon_label = "next 4 weekly observations"
    else:
        horizon_label = f"next 4 periods of about {step_days} days"

    series: list[ForecastPoint] = []
    for index, (observed_at, views) in enumerate(unique):
        predicted_anchor = float(views) if index == len(unique) - 1 else None
        series.append(
            ForecastPoint(observed_at=observed_at.isoformat(), views=float(views), predicted=predicted_anchor)
        )
    last_day = unique[-1][0]
    last_x = float((last_day - origin).days)
    for step in range(1, horizon + 1):
        future_day = last_day + timedelta(days=step_days * step)
        future_x = last_x + step_days * step
        predicted = float(slope * future_x + intercept) if use_linear else float(all_y[-1])
        band = 1.96 * residual_std
        series.append(
            ForecastPoint(
                observed_at=future_day.isoformat(),
                predicted=round(predicted, 2),
                lower=round(max(0.0, predicted - band), 2),
                upper=round(predicted + band, 2),
            )
        )
    generated = (now or datetime.now(timezone.utc)).replace(microsecond=0).isoformat()
    return PredictionResult(
        eligible=True,
        status="forecast",
        message=(
            f"A {method.replace('_', ' ')} forecast was fit on {len(unique)} dated view counts. "
            f"The holdout was the latest {len(test)} observations. "
            "The chart shows that refit extended past the last observation."
        ),
        target="views",
        method=method,
        horizon_label=horizon_label,
        horizon_steps=horizon,
        cadence_days=round(cadence, 2),
        trained=True,
        train_points=len(train),
        test_points=len(test),
        holdout_start=test[0][0].isoformat(),
        baseline_mae=round(naive_mae, 4),
        model_mae=round(linear_mae, 4),
        model_version=MODEL_VERSION,
        generated_at=generated,
        series=series,
        limitations=(
            "The interval is 1.96 times the residual spread of the refit, not a guarantee. "
            "The holdout chose the method. The drawn forecast was then refit on all observations, "
            "so those future points were not part of the error score. "
            "This does not use YouTube's official analytics forecast."
        ),
    )


def _line(x_values: np.ndarray, y_values: np.ndarray) -> tuple[float, float]:
    if len(x_values) < 2 or float(np.std(x_values)) == 0.0:
        return 0.0, float(y_values[-1])
    slope, intercept = np.polyfit(x_values, y_values, 1)
    return float(slope), float(intercept)


def _mae(actual: np.ndarray, predicted: np.ndarray) -> float:
    return float(np.mean(np.abs(actual - predicted)))
