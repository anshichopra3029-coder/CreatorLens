"""Document upload, retrieval, and question routes."""

import asyncio

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import settings
from app.schemas.documents import DocumentAnalysisResponse, DocumentListResponse, QuestionRequest
from app.services.document_analysis import DocumentProcessError, analyze_upload, answer_question
from app.services.document_store import get_document, list_documents
from app.services.upload_service import describe_byte_limit

router = APIRouter()


@router.get("/documents", response_model=DocumentListResponse, tags=["documents"])
def documents() -> DocumentListResponse:
    items = list_documents()
    return DocumentListResponse(count=len(items), documents=items)


@router.get("/documents/{document_id}", response_model=DocumentAnalysisResponse, tags=["documents"])
def document_detail(document_id: str) -> DocumentAnalysisResponse:
    record = get_document(document_id)
    if record is None:
        raise HTTPException(status_code=404, detail="That saved analysis was not found.")
    return record


@router.post("/documents", response_model=DocumentAnalysisResponse, tags=["documents"])
async def create_document(file: UploadFile = File(...)) -> DocumentAnalysisResponse:
    try:
        raw = await _read_bounded(file, settings.max_document_bytes)
        return await asyncio.to_thread(
            analyze_upload,
            raw,
            filename=file.filename or "",
            content_type=file.content_type,
        )
    except DocumentProcessError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.post("/documents/{document_id}/questions", response_model=DocumentAnalysisResponse, tags=["documents"])
async def ask_document(document_id: str, body: QuestionRequest) -> DocumentAnalysisResponse:
    try:
        return await asyncio.to_thread(answer_question, document_id, body.question)
    except DocumentProcessError as exc:
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
            raise DocumentProcessError(413, f"The file is larger than the {limit} document limit.")
        chunks.append(chunk)
    return b"".join(chunks)
