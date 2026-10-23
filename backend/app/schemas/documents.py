"""Responses for saved document analysis.

Numeric CSV fields come from Python. Narrative fields come from Gemini only
when that call succeeds. A missing narrative is null, not a filled-in summary.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.engagement import PostsDatasetCheck

DocumentFormat = Literal["csv", "pdf", "docx"]
DocumentStatus = Literal["analyzed", "extracted", "unreadable"]
NarrativeStatus = Literal["generated", "unavailable", "not_requested"]


class ColumnProfile(BaseModel):
    name: str
    kind: Literal["number", "text", "datetime"]
    non_empty_count: int
    missing_count: int
    numeric_min: float | None = None
    numeric_max: float | None = None
    numeric_mean: float | None = None
    numeric_median: float | None = None


class CategoryStat(BaseModel):
    name: str
    count: int
    avg_engagement_rate: float | None = None
    total_interactions: int | None = None


class TrendStat(BaseModel):
    period: str
    label: str
    count: int
    avg_engagement_rate: float | None = None
    total_interactions: int | None = None


class AnomalyStat(BaseModel):
    row_number: int
    column: str
    value: float
    reason: str


class CsvProfile(BaseModel):
    row_count: int
    column_count: int
    columns: list[ColumnProfile]
    engagement_available: bool
    metric_name: str | None = None
    metric_formula: str | None = None
    metric_note: str | None = None
    posts_analyzed: int | None = None
    avg_engagement_rate: float | None = None
    total_interactions: int | None = None
    best_category: str | None = None
    categories: list[CategoryStat] = Field(default_factory=list)
    trends: list[TrendStat] = Field(default_factory=list)
    anomalies: list[AnomalyStat] = Field(default_factory=list)
    sample_rows: list[dict[str, str]] = Field(default_factory=list)


class GeminiNarrative(BaseModel):
    subject: str = Field(description="What the document is about, using only its contents.")
    summary: str = Field(description="A short summary grounded in the document or the supplied statistics.")
    main_points: list[str]
    key_findings: list[str]
    facts: list[str] = Field(description="Facts or figures that appear in the source. Do not invent any.")
    dates: list[str]
    entities: list[str]
    risks: list[str]
    recommendations: list[str] = Field(description="Actions supported by the document. Do not give generic advice.")


class GeminiAnswer(BaseModel):
    answer: str
    cited_evidence: str = Field(description="A short passage or statistic that supports the answer.")
    uncertainty_note: str


class QuestionRecord(BaseModel):
    id: str
    question: str
    answer: str
    cited_evidence: str
    uncertainty_note: str
    created_at: str


class DocumentAnalysisResponse(BaseModel):
    id: str
    filename: str
    format: DocumentFormat
    size_bytes: int
    created_at: str
    status: DocumentStatus
    file_saved: Literal[True] = True
    analysis_performed: bool
    is_demo: Literal[False] = False
    narrative_status: NarrativeStatus
    narrative_message: str
    subject: str | None = None
    summary: str | None = None
    main_points: list[str] = Field(default_factory=list)
    key_findings: list[str] = Field(default_factory=list)
    facts: list[str] = Field(default_factory=list)
    dates: list[str] = Field(default_factory=list)
    entities: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    text_preview: str = ""
    csv_profile: CsvProfile | None = None
    posts_dataset: PostsDatasetCheck | None = None
    questions: list[QuestionRecord] = Field(default_factory=list)
    model: str | None = None


class DocumentListItem(BaseModel):
    id: str
    filename: str
    format: DocumentFormat
    size_bytes: int
    created_at: str
    status: DocumentStatus
    file_saved: Literal[True] = True
    analysis_performed: bool
    summary: str | None = None


class DocumentListResponse(BaseModel):
    count: int
    documents: list[DocumentListItem]


class QuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)
