"""Forecast results. A forecast is returned only after a real fit on dated observations."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ForecastPoint(BaseModel):
    observed_at: str
    views: float | None = None
    predicted: float | None = None
    lower: float | None = None
    upper: float | None = None


class HorizonForecast(BaseModel):
    label: str
    hours: int
    target_at: str
    supported: bool
    predicted_views: int | None = None
    added_views: int | None = None
    growth_percent: float | None = None
    note: str = ""


class ModelMetric(BaseModel):
    name: Literal["holt_linear", "naive_last_value"]
    label: str
    mae: float | None = None
    growth_wape: float | None = None
    pairs: int = 0
    available: bool = True
    note: str = ""


class PredictionResult(BaseModel):
    eligible: bool
    status: Literal["forecast", "insufficient_data"]
    message: str
    target: str | None = None
    method: str | None = None
    model_label: str | None = None
    selection: Literal["evaluated", "provisional"] | None = None
    selection_reason: str | None = None
    horizon_label: str | None = None
    horizon_steps: int | None = None
    cadence_days: float | None = None
    resample_step_hours: float | None = None
    trained: bool = False
    observations_used: int | None = None
    train_points: int | None = None
    test_points: int | None = None
    evaluation_origins: int | None = None
    holdout_start: str | None = None
    latest_observed_at: str | None = None
    latest_views: int | None = None
    baseline_mae: float | None = None
    model_mae: float | None = None
    metrics: list[ModelMetric] = Field(default_factory=list)
    horizons: list[HorizonForecast] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_version: str = "holt-naive-v2"
    generated_at: str | None = None
    series: list[ForecastPoint] = Field(default_factory=list)
    limitations: str


class ViewObservation(BaseModel):
    observed_at: str
    views: int
    source: Literal["analysis", "csv", "snapshot"]


class TrackedVideo(BaseModel):
    video_id: str
    title: str
    channel_title: str
    thumbnail_url: str | None = None
    latest_analysis_id: str
    analyses: int
    observations: int
    latest_observed_at: str | None = None
    latest_views: int | None = None


class TrackedVideoList(BaseModel):
    count: int
    videos: list[TrackedVideo]


class VideoForecastResponse(BaseModel):
    video_id: str
    title: str
    channel_title: str
    latest_analysis_id: str
    observations: list[ViewObservation]
    prediction: PredictionResult
    guidance: str


class ObservationImportResult(BaseModel):
    video_id: str
    rows_read: int
    inserted: int
    skipped_existing: int
    warnings: list[str] = Field(default_factory=list)
    forecast: VideoForecastResponse


INSUFFICIENT_LIMITATIONS = (
    "Not enough data yet, so no forecast was made. A forecast needs at least three view counts for the same video, "
    "recorded at different times. Once there are six, we also test which forecast method is more accurate on your "
    "real past counts. Saving the same snapshot twice doesn't count."
)


def insufficient_prediction(message: str, *, warnings: list[str] | None = None) -> PredictionResult:
    return PredictionResult(
        eligible=False,
        status="insufficient_data",
        message=message,
        trained=False,
        warnings=warnings or [],
        limitations=INSUFFICIENT_LIMITATIONS,
    )
