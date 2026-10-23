"""Engagement-rate model contracts.

The model predicts a post's view-based engagement rate from fields known
before publication. Outcome counts (views, likes, comments, shares) are used
only to build the training target, never as inputs.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

ModelName = Literal["dummy_mean", "decision_tree", "random_forest", "xgboost"]


class ModelScore(BaseModel):
    name: ModelName
    label: str
    mae: float
    rmse: float


class FeatureImportance(BaseModel):
    feature: str
    label: str
    importance: float
    spread: float


class GroupObservation(BaseModel):
    feature: str
    value: str
    posts: int
    mean_rate: float


class TargetSummary(BaseModel):
    mean: float
    median: float
    minimum: float
    maximum: float


class EngagementModelInfo(BaseModel):
    model_id: str
    source_kind: Literal["document", "demo", "file"]
    source_id: str | None = None
    source_label: str
    trained_at: str
    target: str = "engagement_rate"
    target_formula: str
    target_unit: str = "percentage points"
    features: list[str]
    feature_labels: dict[str, str]
    categories: dict[str, list[str]] = Field(default_factory=dict)
    rows_used: int
    rows_dropped: int
    drop_reasons: list[str] = Field(default_factory=list)
    excluded_columns: list[str] = Field(default_factory=list)
    split: Literal["chronological", "random"]
    train_rows: int
    holdout_rows: int
    holdout_start: str | None = None
    scores: list[ModelScore]
    selected_model: ModelName
    selected_label: str
    beats_baseline: bool
    importance: list[FeatureImportance] = Field(default_factory=list)
    observations: list[GroupObservation] = Field(default_factory=list)
    target_summary: TargetSummary
    limitations: list[str] = Field(default_factory=list)
    library_versions: dict[str, str] = Field(default_factory=dict)


class EngagementModelList(BaseModel):
    count: int
    models: list[EngagementModelInfo]


class PostsDatasetCheck(BaseModel):
    """Whether a saved CSV can train the engagement model, and why not when it cannot."""

    eligible: bool
    total_rows: int = 0
    usable_rows: int = 0
    min_rows: int = 30
    features: list[str] = Field(default_factory=list)
    missing_columns: list[str] = Field(default_factory=list)
    message: str


class TrainingDataset(BaseModel):
    document_id: str
    filename: str
    created_at: str
    check: PostsDatasetCheck


class TrainingDatasetList(BaseModel):
    count: int
    eligible_count: int
    datasets: list[TrainingDataset]


class TrainRequest(BaseModel):
    source: Literal["document", "demo"] = "document"
    document_id: str | None = Field(default=None, max_length=64)


class PredictionInput(BaseModel):
    platform: str | None = Field(default=None, max_length=60)
    category: str | None = Field(default=None, max_length=80)
    posted_at: str | None = Field(default=None, max_length=40)
    posting_hour: int | None = Field(default=None, ge=0, le=23)
    title: str | None = Field(default=None, max_length=300)
    duration_seconds: float | None = Field(default=None, ge=0, le=86_400)


class Contribution(BaseModel):
    feature: str
    label: str
    value: float


class HistoricalContext(BaseModel):
    training_mean: float
    training_median: float
    matching_groups: list[GroupObservation] = Field(default_factory=list)


class EngagementPrediction(BaseModel):
    model_id: str
    model_name: ModelName
    model_label: str
    target: str
    target_formula: str
    target_unit: str
    predicted_engagement_rate: float
    typical_error: float
    band_low: float
    band_high: float
    inputs_used: dict[str, str | float]
    warnings: list[str] = Field(default_factory=list)
    base_value: float | None = None
    contributions: list[Contribution] | None = None
    contribution_note: str
    historical: HistoricalContext
    disclaimer: str = (
        "This is an estimate based on patterns in the posts the model learned from. "
        "It is not a guarantee, and a pattern doesn't prove that changing something (like the title or posting day) "
        "will change your engagement."
    )
