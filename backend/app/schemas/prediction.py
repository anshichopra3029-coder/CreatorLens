"""Forecast results. A forecast is stored only after a real fit on dated observations."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ForecastPoint(BaseModel):
    observed_at: str
    views: float | None = None
    predicted: float | None = None
    lower: float | None = None
    upper: float | None = None


class PredictionResult(BaseModel):
    eligible: bool
    status: Literal["forecast", "insufficient_data"]
    message: str
    target: str | None = None
    method: str | None = None
    horizon_label: str | None = None
    horizon_steps: int | None = None
    cadence_days: float | None = None
    trained: bool = False
    train_points: int | None = None
    test_points: int | None = None
    holdout_start: str | None = None
    baseline_mae: float | None = None
    model_mae: float | None = None
    model_version: str = "baseline-views-v1"
    generated_at: str | None = None
    series: list[ForecastPoint] = Field(default_factory=list)
    limitations: str


def insufficient_prediction(message: str) -> PredictionResult:
    return PredictionResult(
        eligible=False,
        status="insufficient_data",
        message=message,
        trained=False,
        limitations=(
            "No model was trained. A forecast needs at least eight dated view counts for one video, "
            "split chronologically into training and holdout observations."
        ),
    )
