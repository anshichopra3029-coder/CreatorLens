"""CreatorLens API.

Dashboard routes serve labelled demo data calculated from the built-in CSV.
``POST /api/upload`` validates a real CSV and does not store or analyze it.
Video analysis is a separate route and calls Gemini only when configured.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.api.video_routes import router as video_router
from app.core.config import settings

app = FastAPI(
    title="CreatorLens API",
    version="0.1.0",
    summary="Demo analytics, CSV validation, and optional Gemini video analysis.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
)

app.include_router(router, prefix="/api")
app.include_router(video_router, prefix="/api")


@app.get("/", tags=["health"])
def service_index() -> dict[str, str]:
    return {
        "service": "creatorlens-api",
        "health": "/api/health",
        "ai_status": "/api/ai/status",
        "docs": "/docs",
    }
