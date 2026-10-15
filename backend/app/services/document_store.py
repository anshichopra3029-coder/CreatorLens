"""SQLite store for uploaded documents and their analyses.

A row is inserted only after the original file has been written. Callers must
not report file_saved unless insert_document returns.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from app.core.config import settings
from app.schemas.documents import DocumentAnalysisResponse, DocumentListItem, QuestionRecord

_SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    format TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    stored_path TEXT NOT NULL,
    created_at TEXT NOT NULL,
    payload TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS questions (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    cited_evidence TEXT NOT NULL,
    uncertainty_note TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (document_id) REFERENCES documents(id)
);
"""


def files_dir() -> Path:
    path = settings.data_dir / "files"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _connect() -> sqlite3.Connection:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(settings.data_dir / "documents.sqlite", timeout=10)
    connection.row_factory = sqlite3.Row
    connection.executescript(_SCHEMA)
    return connection


def insert_document(record: DocumentAnalysisResponse, stored_path: Path, extracted_text: str) -> None:
    if not stored_path.is_file():
        raise RuntimeError("The document file was not written, so it was not recorded.")
    payload = record.model_dump(mode="json")
    payload["questions"] = []
    payload["extracted_text"] = extracted_text
    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO documents (id, filename, format, size_bytes, stored_path, created_at, payload)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.id,
                record.filename,
                record.format,
                record.size_bytes,
                str(stored_path),
                record.created_at,
                json.dumps(payload),
            ),
        )


def list_documents() -> list[DocumentListItem]:
    with _connect() as connection:
        rows = connection.execute(
            "SELECT payload FROM documents ORDER BY created_at DESC"
        ).fetchall()
    items: list[DocumentListItem] = []
    for row in rows:
        payload = json.loads(row["payload"])
        items.append(DocumentListItem.model_validate(payload))
    return items


def get_document(document_id: str) -> DocumentAnalysisResponse | None:
    with _connect() as connection:
        row = connection.execute(
            "SELECT payload FROM documents WHERE id = ?",
            (document_id,),
        ).fetchone()
        if row is None:
            return None
        questions = connection.execute(
            """
            SELECT id, question, answer, cited_evidence, uncertainty_note, created_at
            FROM questions WHERE document_id = ? ORDER BY created_at ASC
            """,
            (document_id,),
        ).fetchall()
    payload = json.loads(row["payload"])
    payload["questions"] = [dict(item) for item in questions]
    return DocumentAnalysisResponse.model_validate(payload)


def stored_text(document_id: str) -> str | None:
    with _connect() as connection:
        row = connection.execute(
            "SELECT payload FROM documents WHERE id = ?",
            (document_id,),
        ).fetchone()
    if row is None:
        return None
    payload = json.loads(row["payload"])
    text = payload.get("extracted_text")
    return text if isinstance(text, str) else ""


def add_question(document_id: str, record: QuestionRecord) -> None:
    with _connect() as connection:
        found = connection.execute(
            "SELECT id FROM documents WHERE id = ?",
            (document_id,),
        ).fetchone()
        if found is None:
            raise KeyError(document_id)
        connection.execute(
            """
            INSERT INTO questions
            (id, document_id, question, answer, cited_evidence, uncertainty_note, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.id,
                document_id,
                record.question,
                record.answer,
                record.cited_evidence,
                record.uncertainty_note,
                record.created_at,
            ),
        )
