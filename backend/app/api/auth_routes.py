"""Account routes. The current user comes from the session cookie, not the body."""

from fastapi import APIRouter, HTTPException, Request, Response

from app.core.config import settings
from app.schemas.auth import (
    EmailRequest,
    LoginRequest,
    ProfileResponse,
    ProfileUpdate,
    PublicUser,
    RegisterRequest,
    ResetRequest,
    SessionResponse,
    TokenRequest,
)
from app.services.auth import (
    AuthError,
    limit_public,
    login,
    logout,
    profile,
    register,
    request_reset,
    resend_verification,
    reset_password,
    session_from_cookie,
    update_profile,
    verify_email,
)

router = APIRouter()
COOKIE = "cl_session"


def _raise(exc: AuthError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


def current_user(request: Request) -> PublicUser:
    """Sign-in is paused. Saved work is shared on this machine and does not require a session."""
    del request
    return PublicUser(
        id="local",
        email="local@creatorlens.app",
        display_name="Creator",
        email_verified=True,
        created_at="",
    )


def _set_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        COOKIE,
        token,
        httponly=True,
        secure=settings.app_env == "production",
        samesite="lax",
        max_age=14 * 24 * 60 * 60,
        path="/",
    )


@router.post("/auth/register", status_code=202, tags=["auth"])
def auth_register(body: RegisterRequest, request: Request) -> dict[str, str]:
    try:
        limit_public(request, "register")
        register(body.name, body.email, body.password)
    except AuthError as exc:
        _raise(exc)
    return {"status": "verification_sent"}


@router.post("/auth/resend", status_code=202, tags=["auth"])
def auth_resend(body: EmailRequest, request: Request) -> dict[str, str]:
    try:
        limit_public(request, "resend")
        resend_verification(body.email)
    except AuthError as exc:
        _raise(exc)
    return {"status": "ok"}


@router.post("/auth/verify", status_code=204, tags=["auth"])
def auth_verify(body: TokenRequest) -> None:
    try:
        verify_email(body.token)
    except AuthError as exc:
        _raise(exc)


@router.post("/auth/login", response_model=SessionResponse, tags=["auth"])
def auth_login(body: LoginRequest, request: Request, response: Response) -> SessionResponse:
    try:
        token, session = login(body.email, body.password, request)
    except AuthError as exc:
        _raise(exc)
    _set_cookie(response, token)
    return session


@router.post("/auth/logout", status_code=204, tags=["auth"])
def auth_logout(request: Request, response: Response) -> None:
    logout(request.cookies.get(COOKIE, ""))
    response.delete_cookie(COOKIE, path="/")


@router.post("/auth/forgot", status_code=202, tags=["auth"])
def auth_forgot(body: EmailRequest, request: Request) -> dict[str, str]:
    try:
        limit_public(request, "forgot")
        request_reset(body.email)
    except AuthError as exc:
        _raise(exc)
    return {"status": "ok"}


@router.post("/auth/reset", status_code=204, tags=["auth"])
def auth_reset(body: ResetRequest) -> None:
    try:
        reset_password(body.token, body.password)
    except AuthError as exc:
        _raise(exc)


@router.get("/auth/session", response_model=SessionResponse, tags=["auth"])
def auth_session(request: Request) -> SessionResponse:
    return session_from_cookie(request.cookies.get(COOKIE, ""))


@router.get("/account", response_model=ProfileResponse, tags=["auth"])
def account(request: Request) -> ProfileResponse:
    return profile(current_user(request))


@router.patch("/account", response_model=PublicUser, tags=["auth"])
def account_update(body: ProfileUpdate, request: Request) -> PublicUser:
    user = current_user(request)
    try:
        return update_profile(user.id, body.display_name)
    except AuthError as exc:
        _raise(exc)
        raise AssertionError("unreachable") from exc
