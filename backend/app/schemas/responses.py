"""Response models for the Phase 1 API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.core.metrics import METRIC_FORMULA, METRIC_NAME, METRIC_NOTE


class AppliedFilters(BaseModel):
    category: str | None = None
    platform: str | None = None
    start_date: str | None = None
    end_date: str | None = None


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: Literal["creatorlens-api"] = "creatorlens-api"


class DashboardSummary(BaseModel):
    is_demo: Literal[True] = True
    data_source: Literal["demo"] = "demo"
    metric_name: str = METRIC_NAME
    metric_formula: str = METRIC_FORMULA
    metric_note: str = METRIC_NOTE
    posts_analyzed: int
    avg_engagement_rate: float | None
    total_interactions: int
    best_category: str | None
    applied_filters: AppliedFilters


class TrendPoint(BaseModel):
    period: str
    label: str
    avg_engagement_rate: float | None
    post_count: int
    total_interactions: int


class TrendsResponse(BaseModel):
    is_demo: Literal[True] = True
    data_source: Literal["demo"] = "demo"
    metric_name: str = METRIC_NAME
    metric_formula: str = METRIC_FORMULA
    points: list[TrendPoint]
    applied_filters: AppliedFilters


class GroupMetric(BaseModel):
    name: str
    post_count: int
    avg_engagement_rate: float | None
    total_interactions: int
    avg_views: int | None


class ContentComparisonResponse(BaseModel):
    is_demo: Literal[True] = True
    data_source: Literal["demo"] = "demo"
    metric_name: str = METRIC_NAME
    metric_formula: str = METRIC_FORMULA
    categories: list[GroupMetric]
    platforms: list[GroupMetric]
    applied_filters: AppliedFilters


class PostRecord(BaseModel):
    post_id: str
    title: str
    platform: str
    category: str
    post_datetime: str
    views: int
    likes: int
    comments: int
    shares: int
    followers_gained: int
    engagement_rate: float | None = Field(
        description="view_based_engagement_rate for this post, or null when views are not positive.",
    )


class PostsResponse(BaseModel):
    is_demo: Literal[True] = True
    data_source: Literal["demo"] = "demo"
    metric_name: str = METRIC_NAME
    metric_formula: str = METRIC_FORMULA
    count: int
    posts: list[PostRecord]
    applied_filters: AppliedFilters


class InsightCard(BaseModel):
    id: str
    title: str
    summary: str
    evidence: str


class InsightsResponse(BaseModel):
    is_demo: Literal[True] = True
    data_source: Literal["demo"] = "demo"
    disclaimer: str
    metric_name: str = METRIC_NAME
    metric_formula: str = METRIC_FORMULA
    cards: list[InsightCard]


class ColumnReport(BaseModel):
    present: list[str]
    missing: list[str]


class UploadResponse(BaseModel):
    filename: str
    size_bytes: int
    row_count: int
    column_names: list[str]
    expected_columns: ColumnReport
    validation_message: str
    warnings: list[str]
    is_demo: Literal[False] = False
    data_source: Literal["uploaded_csv"] = "uploaded_csv"
    analysis_performed: Literal[False] = False
    file_saved: Literal[False] = False
