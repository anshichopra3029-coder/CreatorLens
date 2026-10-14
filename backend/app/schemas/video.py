"""Typed video-analysis responses.

The Gemini schema is only the content the model must return. The API response
adds server-side fields such as the model id and whether the file was saved.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

VideoCategory = Literal["Education", "Vlog", "Recipe", "Product Review"]


class EvidencePoint(BaseModel):
    observation: str = Field(description="A specific thing that was seen or heard in the video.")
    timestamp: str = Field(
        description="The moment in MM:SS format. Use an empty string when the moment cannot be located.",
    )


class ObservedStrength(BaseModel):
    criterion: str = Field(description="The evaluation criterion this strength satisfies.")
    observation: str = Field(description="What was seen or heard that meets the criterion.")
    timestamp: str = Field(
        description="The moment in MM:SS format. Use an empty string when the moment cannot be located.",
    )


class ImprovementSuggestion(BaseModel):
    criterion: str = Field(description="The evaluation criterion this suggestion addresses.")
    suggestion: str = Field(description="A concrete change the creator can make.")
    evidence: str = Field(description="The observed moment that makes this suggestion necessary.")
    timestamp: str = Field(
        description="The moment in MM:SS format. Use an empty string when the moment cannot be located.",
    )


class GeminiVideoAnalysis(BaseModel):
    """JSON schema sent to Gemini. Do not add server-only fields here."""

    category: VideoCategory = Field(description="The single best-matching category.")
    summary: str = Field(description="A short description of what the video actually shows and says.")
    strengths: list[ObservedStrength]
    suggestions: list[ImprovementSuggestion]
    evidence: list[EvidencePoint]
    confidence_note: str = Field(
        description="Say what is uncertain, including the category when it is not clear.",
    )


class VideoAnalysisResponse(BaseModel):
    filename: str
    category: VideoCategory
    summary: str
    strengths: list[ObservedStrength]
    suggestions: list[ImprovementSuggestion]
    evidence: list[EvidencePoint]
    confidence_note: str
    criteria_applied: list[str]
    provider: Literal["gemini"] = "gemini"
    model: str
    analysis_performed: Literal[True] = True
    is_demo: Literal[False] = False
    file_saved: Literal[False] = False


class AiStatusResponse(BaseModel):
    status: Literal["configured", "not_configured", "sdk_missing"]
    provider: Literal["gemini"] = "gemini"
    model: str
    api_key_configured: bool
    sdk_installed: bool
    sdk_version: str | None = None
    video_input_documented: Literal[True] = True
    live_call_made: Literal[False] = False
    message: str
