"""Video analysis routes. CSV routes stay in routes.py."""

import asyncio

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import settings
from app.schemas.video import AiStatusResponse, VideoAnalysisResponse
from app.services.upload_service import describe_byte_limit
from app.services.video_analysis import (
    MISSING_API_KEY_DETAIL,
    SDK_MISSING_DETAIL,
    VideoAnalysisError,
    ai_status,
    analyze_video_bytes,
    gemini_sdk_info,
    resolve_video_mime,
)

router = APIRouter()


@router.get("/ai/status", response_model=AiStatusResponse, tags=["video"])
def ai_configuration_status() -> AiStatusResponse:
    return ai_status()


@router.post("/videos/analyze", response_model=VideoAnalysisResponse, tags=["video"])
async def analyze_video(file: UploadFile = File(...)) -> VideoAnalysisResponse:
    if not settings.gemini_api_key:
        raise HTTPException(status_code=503, detail=MISSING_API_KEY_DETAIL)
    if not gemini_sdk_info()[0]:
        raise HTTPException(status_code=503, detail=SDK_MISSING_DETAIL)
    filename = file.filename or ""
    try:
        mime_type = resolve_video_mime(filename, file.content_type)
        raw = await _read_bounded(file, settings.max_video_bytes)
        return await asyncio.to_thread(
            analyze_video_bytes,
            raw,
            filename=filename,
            mime_type=mime_type,
        )
    except VideoAnalysisError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


async def _read_bounded(upload: UploadFile, max_bytes: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await upload.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            limit = describe_byte_limit(max_bytes)
            raise VideoAnalysisError(
                413,
                f"The video is larger than the {limit} upload limit.",
            )
        chunks.append(chunk)
    return b"".join(chunks)
