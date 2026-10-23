"""Holt versus last-value forecasts on chronological history. No live API calls."""

from datetime import date, datetime, timedelta, timezone

from app.services.prediction import (
    Observation,
    clean_observations,
    forecast_from_history,
    forecast_observations,
    forecast_views,
    views_per_day,
)

START = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _series(values: list[int], *, hours: list[float] | None = None) -> list[Observation]:
    offsets = hours if hours is not None else [24.0 * index for index in range(len(values))]
    return [Observation(START + timedelta(hours=offset), value) for offset, value in zip(offsets, values, strict=True)]


def test_one_snapshot_does_not_train_a_model():
    result, warnings = forecast_from_history([("2026-01-01T00:00:00+00:00", 100)])
    assert result.trained is False
    assert result.eligible is False
    assert result.series == []
    assert result.horizons == []
    assert warnings == []
    assert "one recorded view count" in result.message


def test_two_snapshots_are_still_insufficient():
    result = forecast_observations(_series([100, 150]))
    assert result.status == "insufficient_data"
    assert "At least 3" in result.message


def test_few_observations_give_a_provisional_naive_forecast():
    result = forecast_observations(_series([100, 160, 230, 300]))
    assert result.eligible is True
    assert result.selection == "provisional"
    assert result.method == "naive_last_value"
    assert all(metric.available is False for metric in result.metrics)
    assert result.baseline_mae is None and result.model_mae is None
    supported = [item for item in result.horizons if item.supported]
    assert supported and all(item.predicted_views == 300 for item in supported)
    assert all(item.added_views == 0 for item in supported)


def test_steady_growth_selects_holt_on_the_rolling_backtest():
    result = forecast_observations(_series([1000 + 250 * day for day in range(12)]))
    assert result.selection == "evaluated"
    assert result.method == "holt_linear"
    holt, naive = result.metrics
    assert holt.name == "holt_linear" and naive.name == "naive_last_value"
    assert holt.mae is not None and naive.mae is not None and holt.mae < 0.9 * naive.mae
    assert naive.growth_wape == 100.0
    assert holt.pairs == naive.pairs > 0
    assert result.evaluation_origins and result.evaluation_origins > 1
    day_one = next(item for item in result.horizons if item.hours == 24)
    week = next(item for item in result.horizons if item.hours == 168)
    assert abs(day_one.predicted_views - (result.latest_views + 250)) <= 25
    assert week.predicted_views > day_one.predicted_views
    assert day_one.growth_percent is not None and day_one.growth_percent > 0
    assert result.latest_observed_at == (START + timedelta(days=11)).isoformat()


def test_unchanged_and_zero_views_keep_the_baseline():
    for value in (0, 40):
        result = forecast_observations(_series([value] * 10))
        assert result.selection == "evaluated"
        assert result.method == "naive_last_value"
        assert all(item.predicted_views == value for item in result.horizons if item.supported)
        naive = result.metrics[1]
        assert naive.mae == 0
        assert naive.growth_wape is None


def test_noisy_flat_history_does_not_promote_holt():
    values = [5000, 5004, 5001, 5006, 5002, 5005, 5003, 5006, 5004, 5007]
    result = forecast_observations(_series(values))
    assert result.selection == "evaluated"
    assert result.method == "naive_last_value"
    assert "not at least 10% better" in (result.selection_reason or "") or "baseline" in (result.selection_reason or "")


def test_irregular_intervals_are_resampled_by_time_not_by_row():
    hours = [0, 2, 3, 30, 31, 55, 80, 81, 104, 130]
    values = [int(100 + 10 * hour) for hour in hours]
    result = forecast_observations(_series(values, hours=hours))
    assert result.resample_step_hours == 12
    assert result.method == "holt_linear"
    day_one = next(item for item in result.horizons if item.hours == 24)
    assert abs(day_one.added_views - 240) <= 40


def test_short_time_span_hides_long_horizons():
    result = forecast_observations(_series([100, 110, 125, 135, 150, 160, 170], hours=[0, 4, 8, 12, 16, 20, 24]))
    labels = {item.label: item for item in result.horizons}
    assert labels["24 hours"].supported is True
    assert labels["3 days"].supported is False
    assert labels["7 days"].supported is False
    assert "twice" in labels["7 days"].note


def test_history_shorter_than_twelve_hours_has_no_forecast():
    result = forecast_observations(_series([100, 120, 140], hours=[0, 1, 2]))
    assert result.status == "insufficient_data"
    assert "cover only" in result.message


def test_forecast_never_drops_below_the_latest_count():
    values = [1000, 1400, 1700, 1900, 2000, 2050, 2070, 2080, 2085, 2087]
    result = forecast_observations(_series(values))
    assert all(item.predicted_views >= 2087 for item in result.horizons if item.supported)


def test_cleaning_drops_invalid_rows_and_same_time_duplicates():
    observations, notes = clean_observations(
        [
            ("2026-01-02T00:00:00Z", 200),
            ("not-a-date", 300),
            ("2026-01-01", None),
            ("2026-01-01", 100),
            ("2026-01-02T00:00:00+00:00", 210),
            ("2026-01-03", -5),
        ]
    )
    assert [(item.observed_at.isoformat(), item.views) for item in observations] == [
        ("2026-01-01T00:00:00+00:00", 100),
        ("2026-01-02T00:00:00+00:00", 210),
    ]
    assert any("ignored" in note for note in notes)
    assert any("shared a timestamp" in note for note in notes)


def test_daily_dates_still_work_for_analytics_files():
    start = date(2026, 1, 1)
    result = forecast_views([(start + timedelta(days=offset), (offset + 1) * 10) for offset in range(10)])
    assert result.method == "holt_linear"
    assert result.model_version == "holt-naive-v2"
    observed = [point for point in result.series if point.views is not None]
    predicted = [point for point in result.series if point.views is None]
    assert observed[-1].observed_at == "2026-01-10T00:00:00+00:00"
    assert predicted[0].observed_at == "2026-01-11T00:00:00+00:00"
    assert abs(predicted[0].predicted - 110) <= 2


def test_views_per_day_uses_publication_age_and_skips_a_missing_date():
    published = "2026-01-01T00:00:00+00:00"
    now = datetime(2026, 1, 11, tzinfo=timezone.utc)
    assert views_per_day(100, published, now) == 10
    assert views_per_day(100, None, now) is None
    assert views_per_day(None, published, now) is None
