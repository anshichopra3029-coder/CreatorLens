"""Forecast eligibility and chronological evaluation. No live API calls."""

from datetime import date, timedelta

from app.services.prediction import forecast_from_history, forecast_views, views_per_day


def test_one_snapshot_does_not_train_a_model():
    result, warnings = forecast_from_history([("2026-01-01T00:00:00+00:00", 100)])
    assert result.trained is False
    assert result.eligible is False
    assert result.series == []
    assert warnings == []
    assert "No model was trained" in result.message


def test_linear_history_beats_the_naive_baseline_on_a_chronological_holdout():
    start = date(2026, 1, 1)
    observations = [(start + timedelta(days=offset), (offset + 1) * 10) for offset in range(10)]
    result = forecast_views(observations)
    assert result.trained is True
    assert result.eligible is True
    assert result.method == "linear_regression"
    assert result.test_points == 2
    assert result.holdout_start == "2026-01-09"
    assert result.baseline_mae is not None
    assert result.model_mae == 0
    assert result.baseline_mae > result.model_mae
    assert result.horizon_label == "next 7 days"
    observed = [point for point in result.series if point.views is not None]
    predicted = [point for point in result.series if point.predicted is not None and point.views is None]
    assert observed[-1].observed_at == "2026-01-10"
    assert predicted[0].observed_at == "2026-01-11"
    assert predicted[0].predicted == 110
    assert predicted[0].lower is not None
    assert predicted[0].upper is not None
    assert result.model_version == "baseline-views-v1"


def test_flat_series_keeps_the_last_value_baseline():
    start = date(2026, 1, 1)
    observations = [(start + timedelta(days=offset), 40) for offset in range(8)]
    result = forecast_views(observations)
    assert result.trained is True
    assert result.method == "naive_last_value"
    future = [point for point in result.series if point.views is None]
    assert future
    assert all(point.predicted == 40 for point in future)


def test_views_per_day_uses_publication_age_and_skips_a_missing_date():
    published = "2026-01-01T00:00:00+00:00"
    from datetime import datetime, timezone

    now = datetime(2026, 1, 11, tzinfo=timezone.utc)
    assert views_per_day(100, published, now) == 10
    assert views_per_day(100, None, now) is None
    assert views_per_day(None, published, now) is None
