import os
from dataclasses import dataclass
from urllib.parse import urlsplit


DEVELOPMENT_CORS_ORIGINS = (
    "http://localhost:3000",
    "http://127.0.0.1:3000",
)
SUPPORTED_ENVIRONMENTS = {"development", "test", "production"}
SUPPORTED_QUEUE_BACKENDS = {"background", "rq"}


@dataclass(frozen=True)
class SupabaseAuthSettings:
    issuer: str
    jwks_url: str
    audience: str


def runtime_environment() -> str:
    environment = (os.getenv("TRUTHFIT_ENV") or "development").strip().lower()
    if environment not in SUPPORTED_ENVIRONMENTS:
        supported = ", ".join(sorted(SUPPORTED_ENVIRONMENTS))
        raise RuntimeError(f"TRUTHFIT_ENV must be one of: {supported}.")
    return environment


def analysis_queue_backend() -> str:
    default_backend = "rq" if runtime_environment() == "production" else "background"
    backend = (os.getenv("TRUTHFIT_ANALYSIS_QUEUE") or default_backend).strip().lower()
    if backend not in SUPPORTED_QUEUE_BACKENDS:
        supported = ", ".join(sorted(SUPPORTED_QUEUE_BACKENDS))
        raise RuntimeError(f"TRUTHFIT_ANALYSIS_QUEUE must be one of: {supported}.")
    return backend


def redis_url() -> str:
    value = (os.getenv("REDIS_URL") or "").strip()
    if analysis_queue_backend() == "rq" and not value:
        raise RuntimeError("REDIS_URL is required when TRUTHFIT_ANALYSIS_QUEUE=rq.")
    return value


def allowed_cors_origins() -> list[str]:
    raw_origins = (os.getenv("TRUTHFIT_ALLOWED_ORIGINS") or "").strip()
    if not raw_origins:
        if runtime_environment() == "production":
            raise RuntimeError(
                "TRUTHFIT_ALLOWED_ORIGINS is required when TRUTHFIT_ENV=production."
            )
        return list(DEVELOPMENT_CORS_ORIGINS)

    origins = [_validate_origin(value) for value in raw_origins.split(",") if value.strip()]
    if not origins:
        raise RuntimeError("TRUTHFIT_ALLOWED_ORIGINS must include at least one HTTP(S) origin.")
    return list(dict.fromkeys(origins))


def supabase_auth_settings() -> SupabaseAuthSettings:
    raw_url = (os.getenv("SUPABASE_URL") or "").strip().rstrip("/")
    if not raw_url:
        raise RuntimeError("SUPABASE_URL is required for authenticated API requests.")

    parsed = urlsplit(raw_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.path:
        raise RuntimeError("SUPABASE_URL must be a valid HTTP(S) project URL.")
    if runtime_environment() == "production" and parsed.scheme != "https":
        raise RuntimeError("SUPABASE_URL must use HTTPS in production.")

    issuer = (os.getenv("SUPABASE_JWT_ISSUER") or f"{raw_url}/auth/v1").strip().rstrip("/")
    jwks_url = (
        os.getenv("SUPABASE_JWKS_URL")
        or f"{issuer}/.well-known/jwks.json"
    ).strip()
    audience = (os.getenv("SUPABASE_JWT_AUDIENCE") or "authenticated").strip()
    if not audience:
        raise RuntimeError("SUPABASE_JWT_AUDIENCE cannot be empty.")

    return SupabaseAuthSettings(issuer=issuer, jwks_url=jwks_url, audience=audience)


def _validate_origin(value: str) -> str:
    origin = value.strip().rstrip("/")
    if origin == "*":
        raise RuntimeError("Wildcard CORS origins are not allowed.")

    parsed = urlsplit(origin)
    try:
        port = parsed.port
    except ValueError as exc:
        raise RuntimeError(f"Invalid CORS origin: {value.strip()}") from exc

    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or (port is not None and not 1 <= port <= 65535)
        or parsed.path
        or parsed.query
        or parsed.fragment
    ):
        raise RuntimeError(f"Invalid CORS origin: {value.strip()}")
    return origin
