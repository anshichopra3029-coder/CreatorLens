"""Engagement-rate model: train from a saved posts CSV, list models, and predict."""

import asyncio

from fastapi import APIRouter, HTTPException, Request

from app.api.auth_routes import current_user
from app.schemas.engagement import (
    EngagementModelInfo,
    EngagementModelList,
    EngagementPrediction,
    PredictionInput,
    TrainingDatasetList,
    TrainRequest,
)
from app.services.engagement_model import (
    EngagementModelError,
    get_model,
    list_models,
    list_training_datasets,
    predict,
    train_from_demo,
    train_from_document,
)

router = APIRouter()


@router.get("/predictions/datasets", response_model=TrainingDatasetList, tags=["predictions"])
async def training_datasets(request: Request) -> TrainingDatasetList:
    items = await asyncio.to_thread(list_training_datasets, current_user(request).id)
    return TrainingDatasetList(
        count=len(items),
        eligible_count=sum(1 for item in items if item.check.eligible),
        datasets=items,
    )


@router.get("/predictions/models", response_model=EngagementModelList, tags=["predictions"])
def engagement_models() -> EngagementModelList:
    items = list_models()
    return EngagementModelList(count=len(items), models=items)


@router.get("/predictions/models/{model_id}", response_model=EngagementModelInfo, tags=["predictions"])
def engagement_model(model_id: str) -> EngagementModelInfo:
    try:
        return get_model(model_id)
    except EngagementModelError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.post("/predictions/train", response_model=EngagementModelInfo, tags=["predictions"])
async def train_engagement_model(body: TrainRequest, request: Request) -> EngagementModelInfo:
    user_id = current_user(request).id
    try:
        if body.source == "demo":
            return await asyncio.to_thread(train_from_demo)
        if not body.document_id:
            raise EngagementModelError(422, "Choose a saved CSV to train from.")
        return await asyncio.to_thread(train_from_document, body.document_id, user_id=user_id)
    except EngagementModelError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.post("/predictions/models/{model_id}/predict", response_model=EngagementPrediction, tags=["predictions"])
async def predict_engagement(model_id: str, body: PredictionInput) -> EngagementPrediction:
    try:
        return await asyncio.to_thread(predict, model_id, body)
    except EngagementModelError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
