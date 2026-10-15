"""YouTube metadata and analysis routes."""

import asyncio

from fastapi import APIRouter, HTTPException

from app.schemas.youtube import (
    OauthStatus,
    YoutubeAnalysisResponse,
    YoutubeListResponse,
    YoutubePreview,
    YoutubeUrlRequest,
)
from app.services.youtube_analysis import YoutubeProcessError, analyze_video, oauth_status, preview_video
from app.services.youtube_store import get_analysis, list_analyses

router = APIRouter()


@router.get("/youtube/oauth/status", response_model=OauthStatus, tags=["youtube"])
def youtube_oauth_status() -> OauthStatus:
    return oauth_status()


@router.get("/youtube/analyses", response_model=YoutubeListResponse, tags=["youtube"])
def youtube_analyses() -> YoutubeListResponse:
    items = list_analyses()
    return YoutubeListResponse(count=len(items), analyses=items)


@router.get("/youtube/analyses/{analysis_id}", response_model=YoutubeAnalysisResponse, tags=["youtube"])
def youtube_analysis(analysis_id: str) -> YoutubeAnalysisResponse:
    record = get_analysis(analysis_id)
    if record is None:
        raise HTTPException(status_code=404, detail="That saved YouTube analysis was not found.")
    return record


@router.post("/youtube/preview", response_model=YoutubePreview, tags=["youtube"])
async def youtube_preview(body: YoutubeUrlRequest) -> YoutubePreview:
    try:
        return await asyncio.to_thread(preview_video, body.url)
    except YoutubeProcessError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.post("/youtube/analyses", response_model=YoutubeAnalysisResponse, tags=["youtube"])
async def create_youtube_analysis(body: YoutubeUrlRequest) -> YoutubeAnalysisResponse:
    try:
        return await asyncio.to_thread(analyze_video, body.url)
    except YoutubeProcessError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
