"""View forecasts from dated observations of one video.

Two methods are compared:

* Naive baseline: every future view count equals the latest observed count.
* Holt's linear exponential smoothing (statsmodels): a smoothed level plus a
  smoothed trend, both updated at every observation, so the trend can slow down
  or speed up instead of following one fixed straight line.

Holt's model needs equally spaced values. Real snapshots are irregular, so the
cumulative view count is resampled onto a regular grid by time-weighted linear
interpolation between real observations. The grid step is the largest of
1, 3, 6, 12, or 24 hours that is not longer than the median gap between
observations. Nothing is extrapolated before the first or after the last real
observation.

Data rules:

* Fewer than 3 distinct timestamps: no forecast.
* 3 to 5: a provisional last-value forecast. Holt's model is not back-tested,
  because there are not enough later observations to score it.
* 6 or more: rolling-origin back-test. From every origin with at least 4 earlier
  observations, both methods forecast the real observations that follow within
  7 days. Holt's model is selected only if its MAE is at least 10% lower than the
  baseline's. Otherwise the baseline is used.

Horizons longer than twice the time covered by the observations are not shown.
Forecasts are never below the latest observed count, because public view counts
are cumulative.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from statistics import median

import numpy as np

from app.schemas.prediction import (
    ForecastPoint,
    HorizonForecast,
    ModelMetric,
    PredictionResult,
    insufficient_prediction,
)

MODEL_VERSION = "holt-naive-v2"
MIN_FORECAST_POINTS = 3
MIN_EVALUATION_POINTS = 6
MIN_TRAIN_POINTS = 4
MAX_ORIGINS = 12
MAX_GRID_POINTS = 2000
HOLT_ADVANTAGE = 0.9
BACKTEST_WINDOW_HOURS = 168
HORIZONS: tuple[tuple[str, int], ...] = (("24 hours", 24), ("3 days", 72), ("7 days", 168))
STEP_CHOICES_HOURS = (1, 3, 6, 12, 24)
LABELS = {
    "holt_linear": "Trend-following forecast (Holt's method)",
    "naive_last_value": "Simple guess: views stay at the latest count",
}

SINGLE_SNAPSHOT = (
    "This video has one recorded view count so far. One snapshot shows today's total, not whether views are going up. "
    "Record more snapshots over time, or import your view history on the Predictions page. No forecast was made yet."
)


@dataclass(frozen=True)
class Observation:
    observed_at: datetime
    views: int


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


def parse_timestamp(value: object) -> datetime | None:
    """ISO date or datetime. A date means 00:00 UTC. A time without a zone is treated as UTC."""
    if isinstance(value, datetime):
        stamp = value
    elif isinstance(value, date):
        stamp = datetime(value.year, value.month, value.day)
    elif isinstance(value, str) and value.strip():
        text = value.strip().replace("Z", "+00:00")
        try:
            stamp = datetime.fromisoformat(text)
        except ValueError:
            return None
    else:
        return None
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    return stamp.astimezone(timezone.utc)


def clean_observations(points: list[tuple[object, int | None]]) -> tuple[list[Observation], list[str]]:
    """Parse, sort, and de-duplicate. Same-timestamp duplicates keep the last value supplied."""
    notes: list[str] = []
    by_time: dict[datetime, int] = {}
    skipped = 0
    replaced = 0
    for stamp, views in points:
        parsed = parse_timestamp(stamp)
        if parsed is None or views is None or not isinstance(views, (int, float)) or views < 0 or not math.isfinite(views):
            skipped += 1
            continue
        if parsed in by_time and by_time[parsed] != int(views):
            replaced += 1
        by_time[parsed] = int(views)
    if skipped:
        notes.append(f"{skipped} entry(ies) without a valid date or view count were ignored.")
    if replaced:
        notes.append(f"{replaced} entry(ies) shared a timestamp with a different count. We used the last one.")
    ordered = [Observation(stamp, by_time[stamp]) for stamp in sorted(by_time)]
    drops = sum(1 for index in range(1, len(ordered)) if ordered[index].views < ordered[index - 1].views)
    if drops:
        notes.append(
            f"The view count went down {drops} time(s). This can happen when YouTube removes fake or invalid views. "
            "We kept those numbers as recorded."
        )
    return ordered, notes


def forecast_from_history(points: list[tuple[str, int | None]]) -> tuple[PredictionResult, list[str]]:
    """Forecast from (timestamp, views) pairs, for example saved snapshots of one video."""
    observations, notes = clean_observations(points)
    return forecast_observations(observations, notes=notes), notes


def forecast_views(observations: list[tuple[date, int]], *, now: datetime | None = None) -> PredictionResult:
    """Forecast from dated rows such as an analytics CSV. A date is treated as 00:00 UTC."""
    cleaned, notes = clean_observations([(observed, views) for observed, views in observations])
    return forecast_observations(cleaned, now=now, notes=notes)


def forecast_observations(
    observations: list[Observation],
    *,
    now: datetime | None = None,
    notes: list[str] | None = None,
) -> PredictionResult:
    warnings_out = list(notes or [])
    count = len(observations)
    if count == 0:
        return insufficient_prediction("Not enough data yet: there's no dated view count, so no forecast was made.", warnings=warnings_out)
    if count == 1:
        return insufficient_prediction(SINGLE_SNAPSHOT, warnings=warnings_out)
    if count < MIN_FORECAST_POINTS:
        return insufficient_prediction(
            f"Not enough data yet: only {count} view counts were recorded at different times. At least {MIN_FORECAST_POINTS} "
            "are needed before we can show a forecast. Record another snapshot later, or import your view history.",
            warnings=warnings_out,
        )

    latest = observations[-1]
    span_hours = (latest.observed_at - observations[0].observed_at).total_seconds() / 3600
    gaps = [
        (observations[index].observed_at - observations[index - 1].observed_at).total_seconds() / 3600
        for index in range(1, count)
    ]
    step = _grid_step(float(median(gaps)))
    supported_any = any(hours <= 2 * span_hours for _, hours in HORIZONS)
    if not supported_any:
        return insufficient_prediction(
            f"Not enough data yet: the {count} view counts cover only {_duration(span_hours)}. The shortest forecast "
            "(24 hours ahead) needs at least 12 hours of recorded history.",
            warnings=warnings_out,
        )

    holt_metric, naive_metric, origins, holdout_start = _backtest(observations, step)
    evaluated = naive_metric.pairs > 0 and count >= MIN_EVALUATION_POINTS
    method = "naive_last_value"
    if not evaluated:
        selection = "provisional"
        reason = (
            f"Only {count} view counts so far, so we can't yet test which method predicts better. For now, this early "
            f"forecast simply keeps views at the latest count. Once there are {MIN_EVALUATION_POINTS} counts, we'll "
            "compare both methods on your real past counts."
        )
        pending = f"Not tested yet. Needs at least {MIN_EVALUATION_POINTS} view counts."
        holt_metric = ModelMetric(name="holt_linear", label=LABELS["holt_linear"], available=False, note=pending)
        naive_metric = ModelMetric(name="naive_last_value", label=LABELS["naive_last_value"], available=False, note=pending)
    else:
        selection = "evaluated"
        naive_mae = naive_metric.mae or 0.0
        holt_mae = holt_metric.mae
        if not holt_metric.available or holt_mae is None:
            reason = (
                "The trend method couldn't run on every test, so we use the simple guess "
                "(the baseline: views stay at the latest count)."
            )
        elif naive_mae == 0 and holt_mae == 0:
            reason = (
                "Neither method missed in the test, because the view count didn't change. "
                "So we use the simpler one (the baseline: views stay at the latest count)."
            )
        elif holt_mae <= HOLT_ADVANTAGE * naive_mae:
            method = "holt_linear"
            reason = (
                f"When we tested on your past counts, the trend method missed by about {holt_mae:,.0f} views on average "
                f"and the simple guess (baseline) by about {naive_mae:,.0f}. The trend method was at least 10% more "
                "accurate, so we use it."
            )
        else:
            reason = (
                f"When we tested on your past counts, the trend method missed by about {holt_mae:,.0f} views on average "
                f"and the simple guess (baseline) by about {naive_mae:,.0f}. The trend method was not at least 10% better, "
                "so we use the simple guess."
            )

    grid = _resample(observations, step)
    holt_path = None
    if method == "holt_linear":
        max_steps = max(1, round(HORIZONS[-1][1] / step))
        holt_path = _holt_forecast(np.array([value for _, value in grid]), max_steps)
        if holt_path is None:
            method = "naive_last_value"
            reason += " The trend method failed on the final run, so the simple guess (baseline) is shown instead."

    horizons: list[HorizonForecast] = []
    clipped = False
    for label, hours in HORIZONS:
        target_at = latest.observed_at + timedelta(hours=hours)
        if hours > 2 * span_hours:
            horizons.append(
                HorizonForecast(
                    label=label,
                    hours=hours,
                    target_at=target_at.isoformat(),
                    supported=False,
                    note=f"Not shown yet. Your history covers {_duration(span_hours)}, and we only forecast up to twice that far ahead.",
                )
            )
            continue
        predicted = float(latest.views)
        if holt_path is not None:
            raw = float(holt_path[max(1, round(hours / step)) - 1])
            if raw < latest.views:
                clipped = True
            predicted = max(raw, float(latest.views))
        value = int(round(max(0.0, predicted)))
        added = value - latest.views
        horizons.append(
            HorizonForecast(
                label=label,
                hours=hours,
                target_at=target_at.isoformat(),
                supported=True,
                predicted_views=value,
                added_views=added,
                growth_percent=round(added / latest.views * 100, 2) if latest.views > 0 else None,
            )
        )
    if clipped:
        warnings_out.append(
            "The trend method pointed below the latest count. Total views only add up over time, so the forecast was kept at the latest count."
        )

    series = [ForecastPoint(observed_at=item.observed_at.isoformat(), views=float(item.views)) for item in observations]
    series[-1] = series[-1].model_copy(update={"predicted": float(latest.views)})
    series.extend(
        ForecastPoint(observed_at=item.target_at, predicted=float(item.predicted_views))
        for item in horizons
        if item.supported and item.predicted_views is not None
    )
    shown = [item.label for item in horizons if item.supported]
    message = (
        f"{LABELS[method]}, based on {count} recorded view counts. Latest: {latest.views:,} views on "
        f"{latest.observed_at.strftime('%Y-%m-%d %H:%M')} UTC. "
        + ("This is an early forecast and may change as more counts come in. " if selection == "provisional" else "")
        + f"Forecast shown for: {', '.join(shown)}."
    )
    generated = (now or datetime.now(timezone.utc)).replace(microsecond=0).isoformat()
    return PredictionResult(
        eligible=True,
        status="forecast",
        message=message,
        target="views",
        method=method,
        model_label=LABELS[method],
        selection=selection,  # type: ignore[arg-type]
        selection_reason=reason,
        horizon_label=", ".join(shown),
        horizon_steps=len(shown),
        cadence_days=round(float(median(gaps)) / 24, 3),
        resample_step_hours=float(step),
        trained=True,
        observations_used=count,
        train_points=MIN_TRAIN_POINTS if evaluated else count,
        test_points=naive_metric.pairs if evaluated else 0,
        evaluation_origins=origins if evaluated else 0,
        holdout_start=holdout_start if evaluated else None,
        latest_observed_at=latest.observed_at.isoformat(),
        latest_views=latest.views,
        baseline_mae=naive_metric.mae if evaluated else None,
        model_mae=holt_metric.mae if evaluated else None,
        metrics=[holt_metric, naive_metric],
        horizons=horizons,
        warnings=warnings_out,
        model_version=MODEL_VERSION,
        generated_at=generated,
        series=series,
        limitations=(
            "This is an estimate, not a promise. It only uses your recorded view counts, so promotion, YouTube "
            "recommendations, or removed views can change things in ways no forecast can see. We don't draw a likely "
            "range, because we can't calculate one we'd trust. Technical detail: the trend method (Holt's) uses views "
            f"filled in evenly every {step} hour(s) between real counts; those filled-in points aren't extra evidence, "
            "and past test accuracy does not guarantee future accuracy."
        ),
    )


def with_recorded_history(result: PredictionResult, observations: list[Observation]) -> PredictionResult:
    """For a result without a forecast, attach the real recorded counts so a page can still show them."""
    if result.status == "forecast" or not observations:
        return result
    latest = observations[-1]
    return result.model_copy(
        update={
            "observations_used": len(observations),
            "latest_observed_at": latest.observed_at.isoformat(),
            "latest_views": latest.views,
            "series": [ForecastPoint(observed_at=item.observed_at.isoformat(), views=float(item.views)) for item in observations],
            "horizons": [
                HorizonForecast(
                    label=label,
                    hours=hours,
                    target_at=(latest.observed_at + timedelta(hours=hours)).isoformat(),
                    supported=False,
                    note="Not available yet. More view counts on different dates are needed.",
                )
                for label, hours in HORIZONS
            ],
        }
    )


def _backtest(observations: list[Observation], step: int) -> tuple[ModelMetric, ModelMetric, int, str | None]:
    holt_errors: list[float] = []
    naive_errors: list[float] = []
    growth: list[float] = []
    holt_ok = True
    origins_used = 0
    first_target: datetime | None = None
    candidates = list(range(MIN_TRAIN_POINTS - 1, len(observations) - 1))[-MAX_ORIGINS:]
    for index in candidates:
        origin = observations[index]
        targets = [
            item
            for item in observations[index + 1 :]
            if (item.observed_at - origin.observed_at).total_seconds() / 3600 <= BACKTEST_WINDOW_HOURS
        ]
        if not targets:
            continue
        origins_used += 1
        grid = _resample(observations[: index + 1], step)
        hours_needed = [(item.observed_at - origin.observed_at).total_seconds() / 3600 for item in targets]
        path = _holt_forecast(np.array([value for _, value in grid]), max(1, round(max(hours_needed) / step)))
        if path is None:
            holt_ok = False
        for item, hours in zip(targets, hours_needed, strict=True):
            first_target = item.observed_at if first_target is None else min(first_target, item.observed_at)
            naive_errors.append(abs(item.views - origin.views))
            growth.append(max(0.0, float(item.views - origin.views)))
            if path is not None:
                predicted = max(float(origin.views), float(path[max(1, round(hours / step)) - 1]))
                holt_errors.append(abs(item.views - predicted))

    def metric(name: str, errors: list[float], available: bool) -> ModelMetric:
        if not errors or not available:
            return ModelMetric(name=name, label=LABELS[name], pairs=len(errors), available=available and bool(errors))  # type: ignore[arg-type]
        total_growth = sum(growth)
        return ModelMetric(
            name=name,  # type: ignore[arg-type]
            label=LABELS[name],
            mae=round(float(np.mean(errors)), 2),
            growth_wape=round(sum(errors) / total_growth * 100, 2) if total_growth > 0 else None,
            pairs=len(errors),
            note="" if total_growth > 0 else "Not shown, because views didn't go up during the test period.",
        )

    return (
        metric("holt_linear", holt_errors, holt_ok),
        metric("naive_last_value", naive_errors, True),
        origins_used,
        first_target.isoformat() if first_target else None,
    )


def _grid_step(median_gap_hours: float) -> int:
    allowed = [choice for choice in STEP_CHOICES_HOURS if choice <= max(median_gap_hours, 1)]
    return allowed[-1]


def _resample(observations: list[Observation], step: int) -> list[tuple[datetime, float]]:
    first = observations[0].observed_at
    last = observations[-1].observed_at
    times: list[datetime] = []
    cursor = last
    while cursor >= first and len(times) < MAX_GRID_POINTS:
        times.append(cursor)
        cursor -= timedelta(hours=step)
    times.reverse()
    known_x = np.array([item.observed_at.timestamp() for item in observations])
    known_y = np.array([float(item.views) for item in observations])
    values = np.interp(np.array([stamp.timestamp() for stamp in times]), known_x, known_y)
    return list(zip(times, values.tolist(), strict=True))


def _holt_forecast(values: np.ndarray, steps: int) -> np.ndarray | None:
    if len(values) < MIN_FORECAST_POINTS:
        return None
    if float(np.ptp(values)) == 0.0:
        return np.full(steps, float(values[-1]))
    from statsmodels.tsa.holtwinters import Holt

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            fitted = Holt(values.astype(float), initialization_method="estimated").fit()
            path = np.asarray(fitted.forecast(steps), dtype=float)
    except Exception:
        return None
    if not np.all(np.isfinite(path)):
        return None
    return path


def _duration(hours: float) -> str:
    if hours < 48:
        return f"{hours:.0f} hour(s)"
    return f"{hours / 24:.1f} days"
