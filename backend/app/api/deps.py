"""Shared query parsing for demo dashboard routes."""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import HTTPException, Query

from app.services.demo_dataset import DemoQuery


def _clean_label(value: str | None, field: str) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if cleaned == "":
        return None
    if len(cleaned) > 80:
        raise HTTPException(status_code=400, detail=f"{field} is too long.")
    return cleaned


def _clean_date(value: str | None, field: str) -> date | None:
    if value is None or value.strip() == "":
        return None
    try:
        return date.fromisoformat(value.strip())
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"{field} must use the YYYY-MM-DD format.",
        ) from exc


def demo_query(
    category: Annotated[str | None, Query(description="Exact demo category name.")] = None,
    platform: Annotated[str | None, Query(description="Exact demo platform name.")] = None,
    start_date: Annotated[str | None, Query(description="Inclusive start date, YYYY-MM-DD.")] = None,
    end_date: Annotated[str | None, Query(description="Inclusive end date, YYYY-MM-DD.")] = None,
) -> DemoQuery:
    parsed_start = _clean_date(start_date, "start_date")
    parsed_end = _clean_date(end_date, "end_date")
    if parsed_start and parsed_end and parsed_start > parsed_end:
        raise HTTPException(status_code=400, detail="start_date cannot be after end_date.")
    return DemoQuery(
        category=_clean_label(category, "category"),
        platform=_clean_label(platform, "platform"),
        start_date=parsed_start,
        end_date=parsed_end,
    )
