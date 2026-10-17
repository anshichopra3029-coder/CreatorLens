"""YouTube analysis responses.

Measured fields come from public metadata extraction. Narrative fields come from
Gemini only after a successful call. Missing metrics stay null.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.diagnosis import DiagnosisEvidence, PerformanceDiagnosis
from app.schemas.roast import ContentExperiment, VideoRoast
from app.schemas.prediction import PredictionResult, insufficient_prediction

EvidenceSource = Literal["transcript", "metadata", "comments", "statistics"]


class PublicStatistics(BaseModel):
    views: int | None = None
    likes: int | None = None
    comments: int | None = None
    views_available: bool
    likes_available: bool
    comments_available: bool
    engagement_rate: float | None = None
    engagement_formula: str = "(likes + comments) / views * 100"
    engagement_note: str = (
        "Public YouTube engagement uses likes and comments only. "
        "Shares are not in the public video statistics. "
        "A hidden count stays unavailable and is not treated as zero."
    )


class VideoMetadata(BaseModel):
    video_id: str
    url: str
    title: str
    description: str
    channel_title: str
    channel_id: str | None = None
    thumbnail_url: str | None = None
    published_at: str | None = None
    duration_seconds: int | None = None
    privacy_status: str
    category: str | None = None
    tags: list[str] = Field(default_factory=list)


class TranscriptStatus(BaseModel):
    available: bool
    text: str = ""
    reason: str


class AnalyticsAvailability(BaseModel):
    connected: bool
    impressions: int | None = None
    click_through_rate: float | None = None
    audience_retention: list[float] | None = None
    reason: str


class CommentSnippet(BaseModel):
    author: str
    text: str
    like_count: int | None = None


class EvidencePoint(BaseModel):
    claim: str
    evidence: str
    source: EvidenceSource


class YoutubeNarrative(BaseModel):
    executive_summary: str
    intended_audience: str
    main_topic: str
    subtopics: list[str]
    key_takeaways: list[str]
    hook_assessment: str
    hook_evidence: list[EvidencePoint]
    structure_notes: list[str]
    title_assessment: str
    description_assessment: str
    cta_assessment: str
    strengths: list[EvidencePoint]
    weaknesses: list[EvidencePoint]
    recommendations: list[EvidencePoint]
    suggested_titles: list[str]
    thumbnail_concepts: list[str]
    suggested_description: str
    content_ideas: list[str]
    limitations: str


class YoutubePreview(BaseModel):
    metadata: VideoMetadata
    statistics: PublicStatistics
    transcript: TranscriptStatus
    analytics: AnalyticsAvailability
    cached: bool
    views_per_day: float | None = None
    views_per_day_note: str = (
        "Views per day = public view count / days since publication. "
        "It is an average over the video's public life, not a recent daily trend."
    )
    is_demo: Literal[False] = False


class YoutubeAnalysisResponse(BaseModel):
    id: str
    created_at: str
    metadata: VideoMetadata
    statistics: PublicStatistics
    transcript: TranscriptStatus
    analytics: AnalyticsAvailability
    comments_status: Literal["available", "disabled", "unavailable"]
    comments: list[CommentSnippet] = Field(default_factory=list)
    views_per_day: float | None = None
    views_per_day_note: str = (
        "Views per day = public view count / days since publication. "
        "It is an average over the video's public life, not a recent daily trend."
    )
    prediction: PredictionResult = Field(
        default_factory=lambda: insufficient_prediction(
            "No forecast was stored with this analysis. A single public snapshot is not a trained model."
        )
    )
    warnings: list[str] = Field(default_factory=list)
    narrative_status: Literal["generated", "unavailable"]
    narrative_message: str
    narrative: YoutubeNarrative | None = None
    diagnosis_status: Literal["generated", "calculated", "unavailable"] = "unavailable"
    diagnosis_message: str = "No performance diagnosis was stored with this analysis."
    diagnosis: PerformanceDiagnosis | None = None
    diagnosis_evidence: DiagnosisEvidence | None = None
    roasts: dict[str, VideoRoast] = Field(default_factory=dict)
    experiment: ContentExperiment | None = None
    model: str | None = None
    cached_metadata: bool
    file_saved: Literal[True] = True
    is_demo: Literal[False] = False


class YoutubeListItem(BaseModel):
    id: str
    video_id: str
    title: str
    channel_title: str
    thumbnail_url: str | None = None
    created_at: str
    views: int | None = None
    likes: int | None = None
    comments: int | None = None
    engagement_rate: float | None = None
    views_per_day: float | None = None
    prediction_eligible: bool = False
    prediction_message: str = ""
    file_saved: Literal[True] = True


class YoutubeListResponse(BaseModel):
    count: int
    analyses: list[YoutubeListItem]


class YoutubeUrlRequest(BaseModel):
    url: str = Field(min_length=1, max_length=500)


class OauthStatus(BaseModel):
    connected: bool
    oauth_client_configured: bool
    impressions: None = None
    click_through_rate: None = None
    audience_retention: None = None
    reason: str
