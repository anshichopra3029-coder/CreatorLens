"""Saved creator-analytics CSV analyses. Numbers come from the uploaded file."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.diagnosis import DiagnosisEvidence, PerformanceDiagnosis
from app.schemas.prediction import PredictionResult, insufficient_prediction
from app.services.analytics_csv import AnalyticsObservation


class VideoRollup(BaseModel):
    video_id: str
    title: str
    observations: int
    latest_date: str | None = None
    views: int | None = None
    likes: int | None = None
    comments: int | None = None
    shares: int | None = None
    impressions: int | None = None
    click_through_rate: float | None = None
    watch_time_minutes: float | None = None
    average_view_duration_seconds: float | None = None
    subscribers_gained: int | None = None
    engagement_rate: float | None = None
    engagement_formula: str


class AnalyticsSummary(BaseModel):
    video_count: int
    observation_count: int
    total_latest_views: int | None = None
    average_engagement_rate: float | None = None
    engagement_formula: str
    formula_note: str
    videos: list[VideoRollup]


class AnalyticsNarrative(BaseModel):
    executive_summary: str
    strengths: list[str]
    weaknesses: list[str]
    recommendations: list[str]
    content_ideas: list[str]
    next_actions: list[str]
    additional_data: str
    limitations: str


class AnalyticsPreview(BaseModel):
    filename: str
    row_count: int
    video_count: int
    columns: list[str]
    warnings: list[str]
    preview: list[AnalyticsObservation]
    forecast_ready: bool
    forecast_message: str
    is_demo: Literal[False] = False


class AnalyticsAnalysisResponse(BaseModel):
    id: str
    created_at: str
    source: Literal["analytics_csv"] = "analytics_csv"
    filename: str
    summary: AnalyticsSummary
    observations: list[AnalyticsObservation]
    warnings: list[str] = Field(default_factory=list)
    prediction: PredictionResult = Field(
        default_factory=lambda: insufficient_prediction("No forecast was stored with this analysis.")
    )
    narrative_status: Literal["generated", "unavailable"]
    narrative_message: str
    narrative: AnalyticsNarrative | None = None
    diagnosis_status: Literal["generated", "calculated", "unavailable"] = "unavailable"
    diagnosis_message: str = "No performance diagnosis was stored with this analysis."
    diagnosis: PerformanceDiagnosis | None = None
    diagnosis_evidence: DiagnosisEvidence | None = None
    model: str | None = None
    file_saved: Literal[True] = True
    is_demo: Literal[False] = False


class AnalyticsListItem(BaseModel):
    id: str
    filename: str
    created_at: str
    video_count: int
    observation_count: int
    total_latest_views: int | None = None
    average_engagement_rate: float | None = None
    prediction_eligible: bool = False
    prediction_message: str = ""
    file_saved: Literal[True] = True


class AnalyticsListResponse(BaseModel):
    count: int
    analyses: list[AnalyticsListItem]
