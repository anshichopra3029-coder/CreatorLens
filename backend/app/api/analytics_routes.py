"""Creator analytics CSV preview and saved analyses."""

import asyncio

from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from app.api.auth_routes import current_user

from app.core.config import settings
from app.schemas.analytics import AnalyticsAnalysisResponse, AnalyticsListResponse, AnalyticsPreview
from app.services.analytics_analysis import AnalyticsProcessError, analyze_upload, preview_upload
from app.services.analytics_store import get_analysis, list_analyses
from app.services.upload_service import describe_byte_limit

router = APIRouter()


@router.get("/analytics/analyses", response_model=AnalyticsListResponse, tags=["analytics"])
def analytics_analyses(request: Request) -> AnalyticsListResponse:
    items = list_analyses(current_user(request).id)
    return AnalyticsListResponse(count=len(items), analyses=items)


@router.get("/analytics/analyses/{analysis_id}", response_model=AnalyticsAnalysisResponse, tags=["analytics"])
def analytics_analysis(analysis_id: str, request: Request) -> AnalyticsAnalysisResponse:
    record = get_analysis(analysis_id, current_user(request).id)
    if record is None:
        raise HTTPException(status_code=404, detail="That saved analytics file was not found.")
    return record


@router.post("/analytics/preview", response_model=AnalyticsPreview, tags=["analytics"])
async def analytics_preview(file: UploadFile = File(...)) -> AnalyticsPreview:
    try:
        raw = await _read_bounded(file)
        return await asyncio.to_thread(preview_upload, raw, file.filename or "")
    except AnalyticsProcessError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.post("/analytics/analyses", response_model=AnalyticsAnalysisResponse, tags=["analytics"])
async def create_analytics_analysis(request: Request, file: UploadFile = File(...)) -> AnalyticsAnalysisResponse:
    user_id = current_user(request).id
    try:
        raw = await _read_bounded(file)
        return await asyncio.to_thread(analyze_upload, raw, file.filename or "", user_id=user_id)
    except AnalyticsProcessError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


async def _read_bounded(upload: UploadFile) -> bytes:
    chunks: list[bytes] = []
    total = 0
    limit = settings.max_upload_bytes
    while True:
        chunk = await upload.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > limit:
            raise AnalyticsProcessError(413, f"The file is larger than the {describe_byte_limit(limit)} upload limit.")
        chunks.append(chunk)
    return b"".join(chunks)
