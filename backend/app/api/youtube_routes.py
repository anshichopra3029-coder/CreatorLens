"""YouTube metadata and analysis routes."""

import asyncio

from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from app.api.auth_routes import current_user
from app.core.config import settings
from app.schemas.prediction import ObservationImportResult, TrackedVideoList, VideoForecastResponse
from app.services.upload_service import describe_byte_limit
from app.services.view_history import (
    ViewHistoryError,
    import_observations,
    list_tracked,
    record_snapshot,
    video_forecast,
)

from app.schemas.roast import ChallengeRequest, ExperimentUpdate, RoastRequest
from app.schemas.youtube import (
    OauthStatus,
    YoutubeAnalysisResponse,
    YoutubeListResponse,
    YoutubePreview,
    YoutubeUrlRequest,
)
from app.services.roast import RoastError, build_fix, challenge_roast, create_roast, save_experiment, update_experiment
from app.services.youtube_analysis import (
    YoutubeProcessError,
    analyze_video,
    oauth_status,
    preview_video,
    refresh_analysis,
)
from app.services.youtube_store import get_analysis, list_analyses

router = APIRouter()


@router.get("/youtube/oauth/status", response_model=OauthStatus, tags=["youtube"])
def youtube_oauth_status() -> OauthStatus:
    return oauth_status()


@router.get("/youtube/analyses", response_model=YoutubeListResponse, tags=["youtube"])
def youtube_analyses(request: Request) -> YoutubeListResponse:
    items = list_analyses(current_user(request).id)
    return YoutubeListResponse(count=len(items), analyses=items)


@router.get("/youtube/analyses/{analysis_id}", response_model=YoutubeAnalysisResponse, tags=["youtube"])
def youtube_analysis(analysis_id: str, request: Request) -> YoutubeAnalysisResponse:
    record = get_analysis(analysis_id, current_user(request).id)
    if record is None:
        raise HTTPException(status_code=404, detail="That saved YouTube analysis was not found.")
    return record


@router.post("/youtube/preview", response_model=YoutubePreview, tags=["youtube"])
async def youtube_preview(body: YoutubeUrlRequest) -> YoutubePreview:
    try:
        return await asyncio.to_thread(preview_video, body.url)
    except YoutubeProcessError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.post("/youtube/analyses/{analysis_id}/refresh", response_model=YoutubeAnalysisResponse, tags=["youtube"])
async def refresh_youtube_analysis(analysis_id: str, request: Request) -> YoutubeAnalysisResponse:
    user_id = current_user(request).id
    try:
        return await asyncio.to_thread(refresh_analysis, analysis_id, user_id=user_id)
    except YoutubeProcessError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.post("/youtube/analyses/{analysis_id}/roast", response_model=YoutubeAnalysisResponse, tags=["youtube"])
async def youtube_roast(analysis_id: str, body: RoastRequest, request: Request) -> YoutubeAnalysisResponse:
    user_id = current_user(request).id
    try:
        return await asyncio.to_thread(create_roast, analysis_id, body.style, user_id=user_id, force=body.force)
    except RoastError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.post("/youtube/analyses/{analysis_id}/roast/challenge", response_model=YoutubeAnalysisResponse, tags=["youtube"])
async def youtube_roast_challenge(analysis_id: str, body: ChallengeRequest, request: Request) -> YoutubeAnalysisResponse:
    user_id = current_user(request).id
    try:
        return await asyncio.to_thread(
            challenge_roast, analysis_id, body.style, body.question, body.context, user_id=user_id
        )
    except RoastError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.post("/youtube/analyses/{analysis_id}/roast/fix", response_model=YoutubeAnalysisResponse, tags=["youtube"])
async def youtube_roast_fix(analysis_id: str, body: RoastRequest, request: Request) -> YoutubeAnalysisResponse:
    user_id = current_user(request).id
    try:
        return await asyncio.to_thread(build_fix, analysis_id, body.style, user_id=user_id)
    except RoastError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.post("/youtube/analyses/{analysis_id}/experiment", response_model=YoutubeAnalysisResponse, tags=["youtube"])
async def youtube_save_experiment(analysis_id: str, body: RoastRequest, request: Request) -> YoutubeAnalysisResponse:
    user_id = current_user(request).id
    try:
        return await asyncio.to_thread(save_experiment, analysis_id, body.style, user_id=user_id)
    except RoastError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.post("/youtube/analyses/{analysis_id}/experiment/result", response_model=YoutubeAnalysisResponse, tags=["youtube"])
async def youtube_update_experiment(analysis_id: str, body: ExperimentUpdate, request: Request) -> YoutubeAnalysisResponse:
    user_id = current_user(request).id
    try:
        return await asyncio.to_thread(
            update_experiment,
            analysis_id,
            user_id=user_id,
            outcome_note=body.outcome_note,
            follow_up_views=body.follow_up_views,
            completed_task=body.completed_task,
        )
    except RoastError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.get("/youtube/videos", response_model=TrackedVideoList, tags=["forecast"])
async def tracked_youtube_videos(request: Request) -> TrackedVideoList:
    items = await asyncio.to_thread(list_tracked, current_user(request).id)
    return TrackedVideoList(count=len(items), videos=items)


@router.get("/youtube/videos/{video_id}/forecast", response_model=VideoForecastResponse, tags=["forecast"])
async def youtube_video_forecast(video_id: str, request: Request) -> VideoForecastResponse:
    user_id = current_user(request).id
    try:
        return await asyncio.to_thread(video_forecast, video_id, user_id)
    except ViewHistoryError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.post("/youtube/videos/{video_id}/snapshot", response_model=VideoForecastResponse, tags=["forecast"])
async def youtube_video_snapshot(video_id: str, request: Request) -> VideoForecastResponse:
    user_id = current_user(request).id
    try:
        return await asyncio.to_thread(record_snapshot, video_id, user_id)
    except ViewHistoryError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.post("/youtube/videos/{video_id}/observations", response_model=ObservationImportResult, tags=["forecast"])
async def youtube_video_import(video_id: str, request: Request, file: UploadFile = File(...)) -> ObservationImportResult:
    user_id = current_user(request).id
    raw = await file.read(settings.max_upload_bytes + 1)
    if len(raw) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail=f"The file is larger than the {describe_byte_limit(settings.max_upload_bytes)} upload limit.")
    if not (file.filename or "").lower().endswith(".csv"):
        raise HTTPException(status_code=415, detail="Upload a .csv file with observed_at and views columns.")
    try:
        return await asyncio.to_thread(import_observations, video_id, user_id, raw)
    except ViewHistoryError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.post("/youtube/analyses", response_model=YoutubeAnalysisResponse, tags=["youtube"])
async def create_youtube_analysis(body: YoutubeUrlRequest, request: Request) -> YoutubeAnalysisResponse:
    user_id = current_user(request).id
    try:
        return await asyncio.to_thread(analyze_video, body.url, user_id=user_id)
    except YoutubeProcessError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
