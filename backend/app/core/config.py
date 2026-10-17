"""Runtime settings for the API.

Defaults match local Vite on port 5173 and a 5 MB CSV cap, so the API can
start without a .env file. Environment variables override the defaults.
A local backend/.env file fills only variables that are not already set.
"""

from __future__ import annotations

import os
from pathlib import Path


def _load_local_env() -> None:
    """Load backend/.env without overriding existing process variables."""
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.is_file():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key or key in os.environ:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ[key] = value


def _positive_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be a whole number.") from exc
    if value <= 0:
        raise RuntimeError(f"{name} must be greater than zero.")
    return value


def _bounded_float(name: str, default: float, low: float, high: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = float(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be a number.") from exc
    if not low <= value <= high:
        raise RuntimeError(f"{name} must be between {low} and {high}.")
    return value


class Settings:
    def __init__(self) -> None:
        self.app_env = os.getenv("APP_ENV", "development")
        self.frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173").rstrip("/")
        self.max_upload_size_mb = _positive_int("MAX_UPLOAD_SIZE_MB", 5)
        self.max_upload_rows = _positive_int("MAX_UPLOAD_ROWS", 20000)
        self.max_upload_columns = _positive_int("MAX_UPLOAD_COLUMNS", 100)
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
        # Accepted so an older .env line does not crash. Public metadata uses yt-dlp and does not read this value.
        self.youtube_api_key = os.getenv("YOUTUBE_API_KEY", "").strip()
        self.youtube_cache_seconds = _positive_int("YOUTUBE_CACHE_SECONDS", 21600)
        self.youtube_oauth_client_id = os.getenv("YOUTUBE_OAUTH_CLIENT_ID", "").strip()
        self.smtp_host = os.getenv("SMTP_HOST", "").strip()
        self.smtp_port = _positive_int("SMTP_PORT", 587)
        self.smtp_username = os.getenv("SMTP_USERNAME", "").strip()
        self.smtp_password = os.getenv("SMTP_PASSWORD", "").strip()
        self.smtp_from = os.getenv("SMTP_FROM", "").strip()
        self.smtp_tls = os.getenv("SMTP_TLS", "true").strip().lower() not in {"0", "false", "no"}
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip() or "gemini-3.8-flash"
        self.roast_temperature = _bounded_float("ROAST_TEMPERATURE", 1.4, 0.0, 2.0)
        self.max_video_size_mb = _positive_int("MAX_VIDEO_SIZE_MB", 100)
        self.gemini_file_timeout_seconds = _positive_int("GEMINI_FILE_TIMEOUT_SECONDS", 180)
        self.max_document_size_mb = _positive_int("MAX_DOCUMENT_SIZE_MB", 15)
        default_data = Path(__file__).resolve().parents[2] / "data"
        self.data_dir = Path(os.getenv("CREATORLENS_DATA_DIR", str(default_data)))

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def max_video_bytes(self) -> int:
        return self.max_video_size_mb * 1024 * 1024

    @property
    def max_document_bytes(self) -> int:
        return self.max_document_size_mb * 1024 * 1024

    @property
    def cors_origins(self) -> list[str]:
        """Allow the configured Vite origin and its localhost/127.0.0.1 twin.

        Browsers treat those host names as different origins even when they
        point at the same dev server. No other origins are allowed.
        """
        origin = self.frontend_origin
        origins = [origin]
        if "://localhost" in origin:
            origins.append(origin.replace("://localhost", "://127.0.0.1", 1))
        elif "://127.0.0.1" in origin:
            origins.append(origin.replace("://127.0.0.1", "://localhost", 1))
        return list(dict.fromkeys(origins))


_load_local_env()
settings = Settings()
