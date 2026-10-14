"""Send one video to Gemini and validate the structured response.

This module does not invent an analysis. A missing key, a missing SDK, or an
unusable model response raises VideoAnalysisError.
"""

from __future__ import annotations

import logging
import tempfile
import time
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.core.config import settings
from app.schemas.video import (
    AiStatusResponse,
    GeminiVideoAnalysis,
    VideoAnalysisResponse,
)
from app.services.video_criteria import criteria_for, criteria_prompt

logger = logging.getLogger(__name__)

MISSING_API_KEY_DETAIL = (
    "GEMINI_API_KEY is not configured on the server. "
    "Video analysis was not run, and no result was generated."
)
SDK_MISSING_DETAIL = (
    "The Gemini Python SDK is not installed on the server. "
    "Video analysis was not run, and no result was generated."
)

ALLOWED_VIDEO_TYPES = {
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".mov": "video/quicktime",
    ".mpeg": "video/mpeg",
    ".mpg": "video/mpeg",
}


class VideoAnalysisError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def gemini_sdk_info() -> tuple[bool, str | None]:
    try:
        from google import genai  # noqa: F401
    except ImportError:
        return False, None
    try:
        return True, version("google-genai")
    except PackageNotFoundError:
        return True, None


def ai_status() -> AiStatusResponse:
    """Report configuration only. This does not call Gemini or reveal the key."""
    installed, sdk_version = gemini_sdk_info()
    configured = bool(settings.gemini_api_key)
    if not configured:
        status = "not_configured"
        message = MISSING_API_KEY_DETAIL
    elif not installed:
        status = "sdk_missing"
        message = SDK_MISSING_DETAIL
    else:
        status = "configured"
        message = (
            "The Gemini API key is set and the SDK is installed. "
            "This check does not call Gemini and does not confirm that video analysis succeeds."
        )
    return AiStatusResponse(
        status=status,
        model=settings.gemini_model,
        api_key_configured=configured,
        sdk_installed=installed,
        sdk_version=sdk_version,
        message=message,
    )


def resolve_video_mime(filename: str, content_type: str | None) -> str:
    suffix = Path(filename).suffix.lower()
    expected = ALLOWED_VIDEO_TYPES.get(suffix)
    if expected is None:
        allowed = ", ".join(sorted(ALLOWED_VIDEO_TYPES))
        raise VideoAnalysisError(
            415,
            f"Upload a video file ({allowed}). Other file types are rejected.",
        )
    supplied = (content_type or "").split(";", 1)[0].strip().lower()
    if supplied in {"", "application/octet-stream"}:
        return expected
    if supplied != expected:
        raise VideoAnalysisError(
            415,
            f"The file extension {suffix} does not match the content type {supplied}.",
        )
    return expected


def analyze_video_bytes(
    raw: bytes,
    *,
    filename: str,
    mime_type: str,
    client: Any | None = None,
) -> VideoAnalysisResponse:
    if not settings.gemini_api_key:
        raise VideoAnalysisError(503, MISSING_API_KEY_DETAIL)
    if client is None and not gemini_sdk_info()[0]:
        raise VideoAnalysisError(503, SDK_MISSING_DETAIL)
    if len(raw) == 0:
        raise VideoAnalysisError(400, "The uploaded video is empty.")

    safe_name = Path(filename).name or "video"
    suffix = Path(safe_name).suffix.lower() or ".mp4"
    temp_path: str | None = None
    try:
        temp_path = _write_temp(raw, suffix)
        gemini = client if client is not None else _build_client()
        output_text = _request_analysis(gemini, temp_path, mime_type)
        parsed = _parse_model_output(output_text)
    finally:
        if temp_path is not None:
            Path(temp_path).unlink(missing_ok=True)

    return VideoAnalysisResponse(
        filename=safe_name,
        category=parsed.category,
        summary=parsed.summary,
        strengths=parsed.strengths,
        suggestions=parsed.suggestions,
        evidence=parsed.evidence,
        confidence_note=parsed.confidence_note,
        criteria_applied=criteria_for(parsed.category),
        model=settings.gemini_model,
    )


def _write_temp(raw: bytes, suffix: str) -> str:
    handle = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    try:
        handle.write(raw)
    finally:
        handle.close()
    return handle.name


def _build_client() -> Any:
    from google import genai

    return genai.Client(api_key=settings.gemini_api_key)


def _request_analysis(client: Any, video_path: str, mime_type: str) -> str:
    uploaded_name: str | None = None
    try:
        uploaded = client.files.upload(file=video_path, config={"mime_type": mime_type})
        uploaded_name = getattr(uploaded, "name", None)
        ready = _wait_until_active(client, uploaded)
        interaction = client.interactions.create(
            model=settings.gemini_model,
            input=[
                {
                    "type": "video",
                    "uri": ready.uri,
                    "mime_type": getattr(ready, "mime_type", None) or mime_type,
                },
                {"type": "text", "text": _analysis_prompt()},
            ],
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": GeminiVideoAnalysis.model_json_schema(),
            },
        )
        text = getattr(interaction, "output_text", None)
        if not isinstance(text, str) or text.strip() == "":
            raise VideoAnalysisError(
                502,
                "Gemini returned an empty response. No analysis was created.",
            )
        return text
    except VideoAnalysisError:
        raise
    except Exception as exc:
        logger.warning("Gemini video request failed with %s.", type(exc).__name__)
        raise _public_gemini_error(exc) from exc
    finally:
        if uploaded_name:
            try:
                client.files.delete(name=uploaded_name)
            except Exception:
                logger.warning("The temporary Gemini file could not be deleted.")


def _wait_until_active(client: Any, uploaded: Any) -> Any:
    deadline = time.monotonic() + settings.gemini_file_timeout_seconds
    current = uploaded
    while True:
        state = _state_name(current)
        if state == "ACTIVE":
            return current
        if state == "FAILED":
            raise VideoAnalysisError(
                502,
                "Gemini could not process the video file. No analysis was created.",
            )
        if time.monotonic() >= deadline:
            raise VideoAnalysisError(
                502,
                "Gemini did not finish processing the video before the timeout. No analysis was created.",
            )
        time.sleep(5)
        name = getattr(current, "name", None)
        if not name:
            raise VideoAnalysisError(
                502,
                "Gemini did not return a file id for the uploaded video. No analysis was created.",
            )
        current = client.files.get(name=name)


def _state_name(uploaded: Any) -> str:
    state = getattr(uploaded, "state", None)
    if state is None:
        return ""
    if isinstance(state, str):
        return state
    name = getattr(state, "name", None)
    if isinstance(name, str):
        return name
    return str(state)


def _parse_model_output(output_text: str) -> GeminiVideoAnalysis:
    try:
        parsed = GeminiVideoAnalysis.model_validate_json(output_text)
    except ValidationError as exc:
        raise VideoAnalysisError(
            502,
            "Gemini returned a response that did not match the analysis schema. No analysis was created.",
        ) from exc
    if parsed.summary.strip() == "" or parsed.confidence_note.strip() == "":
        raise VideoAnalysisError(
            502,
            "Gemini returned an incomplete analysis. No analysis was created.",
        )
    return parsed


def _analysis_prompt() -> str:
    return (
        "Watch and listen to this video. Return only the structured analysis.\n\n"
        f"{criteria_prompt()}"
    )


def _public_gemini_error(exc: Exception) -> VideoAnalysisError:
    code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
    text = str(exc)
    if code in (401, 403) or "API_KEY_INVALID" in text or "API key not valid" in text:
        return VideoAnalysisError(502, "Gemini rejected the API key. No analysis was created.")
    if code == 404 and "model" in text.lower():
        return VideoAnalysisError(
            502,
            "The configured Gemini model was not found. No analysis was created.",
        )
    return VideoAnalysisError(502, "The Gemini request failed. No analysis was created.")
