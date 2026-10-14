"""Validate an uploaded CSV in memory and return metadata only.

The file is not written to disk, not stored, and not passed to the demo
dashboard. Cell values are never returned.
"""

from __future__ import annotations

import io
from pathlib import Path

import pandas as pd
from fastapi import HTTPException, UploadFile

from app.core.config import settings

EXPECTED_COLUMNS = (
    "post_id",
    "platform",
    "category",
    "post_datetime",
    "views",
    "likes",
    "comments",
    "shares",
    "followers_gained",
)

VALIDATION_MESSAGE = (
    "The CSV was parsed successfully. This check only reports file metadata. "
    "The file was not saved, and no engagement analysis was run."
)


def describe_byte_limit(max_bytes: int) -> str:
    megabyte = 1024 * 1024
    if max_bytes > 0 and max_bytes % megabyte == 0:
        return f"{max_bytes // megabyte} MB"
    if max_bytes >= 1024:
        return f"{max_bytes / 1024:.1f} KB"
    return f"{max_bytes} bytes"


async def _read_bounded(upload: UploadFile, max_bytes: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await upload.read(64 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            limit = describe_byte_limit(max_bytes)
            raise HTTPException(
                status_code=413,
                detail=f"The file is larger than the {limit} upload limit.",
            )
        chunks.append(chunk)
    return b"".join(chunks)


def _parse_csv(raw: bytes) -> pd.DataFrame:
    if len(raw) == 0 or raw.strip() == b"":
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail="The file could not be read as UTF-8 text.",
        ) from exc
    if text.strip() == "":
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    try:
        return pd.read_csv(io.StringIO(text), sep=",", dtype=str, keep_default_na=False)
    except pd.errors.EmptyDataError as exc:
        raise HTTPException(
            status_code=400,
            detail="The CSV has no header row to read.",
        ) from exc
    except pd.errors.ParserError as exc:
        raise HTTPException(
            status_code=400,
            detail=(
                "The CSV could not be parsed. Check that quotes are closed "
                "and each row has a consistent number of columns."
            ),
        ) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail="The CSV could not be parsed.") from exc


def _column_report(columns: list[str]) -> dict[str, list[str]]:
    lookup = {column.casefold() for column in columns if column}
    present = [name for name in EXPECTED_COLUMNS if name.casefold() in lookup]
    missing = [name for name in EXPECTED_COLUMNS if name.casefold() not in lookup]
    return {"present": present, "missing": missing}


async def validate_csv_upload(upload: UploadFile) -> dict[str, object]:
    try:
        filename = Path(upload.filename or "").name.strip()
        if filename.lower() in {"", ".", ".."}:
            raise HTTPException(status_code=400, detail="Choose a CSV file before uploading.")
        if not filename.lower().endswith(".csv"):
            raise HTTPException(status_code=415, detail="Only .csv files are accepted.")
        if len(filename) > 255:
            filename = filename[-255:]

        raw = await _read_bounded(upload, settings.max_upload_bytes)
        frame = _parse_csv(raw)
        columns = [str(column).strip() for column in frame.columns]
        if not columns or all(column == "" for column in columns):
            raise HTTPException(
                status_code=400,
                detail="The CSV needs a header row with column names.",
            )
        if len(columns) > settings.max_upload_columns:
            raise HTTPException(
                status_code=400,
                detail=f"The CSV has too many columns. The limit is {settings.max_upload_columns}.",
            )
        if len(frame) > settings.max_upload_rows:
            raise HTTPException(
                status_code=400,
                detail=f"The CSV has too many rows. The limit is {settings.max_upload_rows}.",
            )

        warnings: list[str] = []
        if any(column.startswith("Unnamed:") or column == "" for column in columns):
            warnings.append("At least one header cell is empty.")
        if len(set(columns)) != len(columns):
            warnings.append("The header contains duplicate column names.")
        report = _column_report(columns)
        if report["missing"]:
            warnings.append(
                "Some columns used by later analysis are missing: " + ", ".join(report["missing"]) + "."
            )
        if len(frame) == 0:
            warnings.append("The file has column headers but no data rows.")

        return {
            "filename": filename,
            "size_bytes": len(raw),
            "row_count": int(len(frame)),
            "column_names": columns,
            "expected_columns": report,
            "validation_message": VALIDATION_MESSAGE,
            "warnings": warnings,
            "is_demo": False,
            "data_source": "uploaded_csv",
            "analysis_performed": False,
            "file_saved": False,
        }
    finally:
        await upload.close()
