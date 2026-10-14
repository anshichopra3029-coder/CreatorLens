"""Thin route handlers. Calculations live in the service modules."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile

from app.api.deps import demo_query
from app.schemas.responses import (
    ContentComparisonResponse,
    DashboardSummary,
    HealthResponse,
    InsightsResponse,
    PostsResponse,
    TrendsResponse,
    UploadResponse,
)
from app.services.demo_dataset import DemoQuery, build_comparison, build_posts, build_summary, build_trends
from app.services.insights_service import build_insights
from app.services.upload_service import validate_csv_upload

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["health"])
def health() -> HealthResponse:
    return HealthResponse()


@router.get("/dashboard/summary", response_model=DashboardSummary, tags=["dashboard"])
def dashboard_summary(query: Annotated[DemoQuery, Depends(demo_query)]) -> DashboardSummary:
    return DashboardSummary.model_validate(build_summary(query))


@router.get("/dashboard/trends", response_model=TrendsResponse, tags=["dashboard"])
def dashboard_trends(query: Annotated[DemoQuery, Depends(demo_query)]) -> TrendsResponse:
    return TrendsResponse.model_validate(build_trends(query))


@router.get(
    "/dashboard/content-comparison",
    response_model=ContentComparisonResponse,
    tags=["dashboard"],
)
def dashboard_content_comparison(
    query: Annotated[DemoQuery, Depends(demo_query)],
) -> ContentComparisonResponse:
    return ContentComparisonResponse.model_validate(build_comparison(query))


@router.get("/posts", response_model=PostsResponse, tags=["posts"])
def posts(query: Annotated[DemoQuery, Depends(demo_query)]) -> PostsResponse:
    return PostsResponse.model_validate(build_posts(query))


@router.get("/insights", response_model=InsightsResponse, tags=["insights"])
def insights() -> InsightsResponse:
    return InsightsResponse.model_validate(build_insights())


@router.post("/upload", response_model=UploadResponse, tags=["upload"])
async def upload_csv(file: UploadFile = File(...)) -> UploadResponse:
    return UploadResponse.model_validate(await validate_csv_upload(file))
