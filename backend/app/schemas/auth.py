"""Account contracts. The password is accepted on input and never returned."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PublicUser(BaseModel):
    id: str
    email: str
    display_name: str
    email_verified: bool
    created_at: str


class SessionResponse(BaseModel):
    authenticated: bool
    verified: bool = False
    csrf_token: str = ""
    user: PublicUser | None = None


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    email: str = Field(min_length=3, max_length=200)
    password: str = Field(min_length=10, max_length=200)


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=200)
    password: str = Field(min_length=1, max_length=200)


class EmailRequest(BaseModel):
    email: str = Field(min_length=3, max_length=200)


class TokenRequest(BaseModel):
    token: str = Field(min_length=20, max_length=300)


class ResetRequest(BaseModel):
    token: str = Field(min_length=20, max_length=300)
    password: str = Field(min_length=10, max_length=200)


class ProfileUpdate(BaseModel):
    display_name: str = Field(min_length=1, max_length=80)


class RecentActivity(BaseModel):
    id: str
    kind: str
    title: str
    created_at: str


class ProfileResponse(BaseModel):
    user: PublicUser
    videos_analyzed: int
    diagnoses_saved: int
    experiments_saved: int
    documents_saved: int
    recent: list[RecentActivity]
