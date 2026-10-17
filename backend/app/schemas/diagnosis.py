"""Performance diagnosis contracts.

Numeric evidence is calculated in application code. The diagnosis prose is
present only after Gemini returns a response that cites that evidence.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

EvidenceLevel = Literal["Limited evidence", "Moderate evidence", "Stronger evidence"]


class PeerMetric(BaseModel):
    video_id: str
    title: str
    engagement_rate: float | None = None


class HistoryPoint(BaseModel):
    observed_at: str
    views: int | None = None


class DiagnosisEvidence(BaseModel):
    subject_id: str
    title: str
    scenario: Literal["single_snapshot", "historical_snapshots", "multi_video"]
    views: int | None = None
    likes: int | None = None
    comments: int | None = None
    shares: int | None = None
    include_shares: bool = False
    engagement_rate: float | None = None
    engagement_formula: str
    like_rate: float | None = None
    comment_rate: float | None = None
    views_per_day: float | None = None
    peer_sample_size: int = 0
    dated_view_points: int = 0
    baseline_rate: float | None = None
    baseline_label: str = ""
    observations: list[str] = Field(default_factory=list)
    unanswered: list[str] = Field(default_factory=list)
    evidence_level: EvidenceLevel
    evidence_reasons: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


ClaimKind = Literal["observed", "inference", "hypothesis"]


class StrengthInsight(BaseModel):
    title: str = Field(min_length=1, max_length=140)
    explanation: str = Field(min_length=1, max_length=500)
    evidence: str = Field(min_length=1, max_length=500)
    baseline: str = Field(default="", max_length=300)
    claim_kind: ClaimKind = "observed"


class ImprovementInsight(BaseModel):
    title: str = Field(min_length=1, max_length=140)
    explanation: str = Field(min_length=1, max_length=500)
    evidence: str = Field(min_length=1, max_length=500)
    possible_causes: list[str] = Field(default_factory=list, max_length=3)
    claim_kind: ClaimKind = "inference"


class ReasonItem(BaseModel):
    statement: str = Field(min_length=1, max_length=400)
    evidence: str = Field(min_length=1, max_length=500)
    claim_kind: Literal["hypothesis"] = "hypothesis"


class ActionItem(BaseModel):
    priority: Literal["High", "Medium", "Low"]
    action: str = Field(min_length=1, max_length=400)
    reason: str = Field(min_length=1, max_length=400)
    evidence: str = Field(min_length=1, max_length=500)
    success_measure: str = Field(min_length=1, max_length=400)


class EvidenceQuality(BaseModel):
    level: EvidenceLevel
    reasons: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class PerformanceDiagnosis(BaseModel):
    summary: str = Field(min_length=1, max_length=800)
    strengths: list[StrengthInsight] = Field(default_factory=list, max_length=3)
    improvements: list[ImprovementInsight] = Field(default_factory=list, max_length=3)
    actions: list[ActionItem] = Field(default_factory=list, max_length=5)
    reasons: list[ReasonItem] = Field(default_factory=list, max_length=4)
    evidence_quality: EvidenceQuality
    source: Literal["evidence_rules", "gemini"] = "evidence_rules"
