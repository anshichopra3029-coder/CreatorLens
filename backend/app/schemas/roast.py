"""Roast and Content Court contracts.

Facts come from the saved public statistics. Jokes may be rewritten by Gemini,
but only when they still match those statistics.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

RoastStyle = Literal["friendly", "savage", "brutal"]
ClaimKind = Literal["observed", "inference", "hypothesis"]


class CourtClue(BaseModel):
    label: str
    detail: str
    source: str
    claim_kind: Literal["observed"] = "observed"


class CourtPoint(BaseModel):
    title: str
    detail: str
    evidence: str
    claim_kind: ClaimKind


class CourtVerdict(BaseModel):
    summary: str
    confidence: Literal["Low confidence", "Moderate confidence", "Higher confidence"]
    why: str
    missing: list[str] = Field(default_factory=list)


class NextMove(BaseModel):
    change: str
    why: str
    metric: str


class FixPack(BaseModel):
    titles: list[str] = Field(default_factory=list)
    thumbnail_concepts: list[str] = Field(default_factory=list)
    hooks: list[str] = Field(default_factory=list)
    note: str


class ChallengeReply(BaseModel):
    question: str
    context: str = ""
    reply: str
    defended_original: Literal[False] = False


class VideoRoast(BaseModel):
    style: RoastStyle
    take: int = 1
    opening: str
    bits: list[str] = Field(default_factory=list)
    closer: str = ""
    observation: str
    limits: str
    bridge: str
    investigation: list[str] = Field(default_factory=list)
    clues: list[CourtClue]
    defence: list[CourtPoint]
    suspects: list[CourtPoint]
    verdict: CourtVerdict
    next_move: NextMove
    fixes: FixPack | None = None
    challenge: ChallengeReply | None = None
    source: Literal["evidence_rules", "gemini"] = "evidence_rules"


class RoastDraft(BaseModel):
    """The shape Gemini is asked to return. Every line is validated before it is kept."""

    opening: str
    bits: list[str] = Field(default_factory=list)
    closer: str = ""


class ContentExperiment(BaseModel):
    id: str
    video_id: str
    issue: str
    proposed_change: str
    metric: str
    created_at: str
    outcome_note: str = ""
    follow_up_views: int | None = None
    completed_task: bool = False
    improvement_shown: Literal[False] = False
    result_note: str = (
        "Marking the task complete does not show that the change improved performance. "
        "A later public view count, if you record one, is still not proof of cause."
    )


class RoastRequest(BaseModel):
    style: RoastStyle = "friendly"
    force: bool = False


class ChallengeRequest(BaseModel):
    style: RoastStyle
    question: str = Field(min_length=1, max_length=500)
    context: str = Field(default="", max_length=500)


class ExperimentUpdate(BaseModel):
    outcome_note: str = Field(default="", max_length=500)
    follow_up_views: int | None = Field(default=None, ge=0)
    completed_task: bool = False
