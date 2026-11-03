import os
from dataclasses import dataclass
from urllib.parse import urlsplit


DEVELOPMENT_CORS_ORIGINS = (
    "http://localhost:3000",
    "http://127.0.0.1:3000",
)
DEVELOPMENT_TRUSTED_HOSTS = ("localhost", "127.0.0.1", "testserver")
SUPPORTED_ENVIRONMENTS = {"development", "test", "production"}
SUPPORTED_QUEUE_BACKENDS = {"background", "rq"}
SUPPORTED_RATE_LIMIT_BACKENDS = {"memory", "redis"}


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
    if (analysis_queue_backend() == "rq" or rate_limit_backend() == "redis") and not value:
        raise RuntimeError(
            "REDIS_URL is required when the analysis queue or rate limiter uses Redis."
        )
    return value


def rate_limit_backend() -> str:
    default_backend = "redis" if runtime_environment() == "production" else "memory"
    backend = (os.getenv("TRUTHFIT_RATE_LIMIT_BACKEND") or default_backend).strip().lower()
    if backend not in SUPPORTED_RATE_LIMIT_BACKENDS:
        supported = ", ".join(sorted(SUPPORTED_RATE_LIMIT_BACKENDS))
        raise RuntimeError(f"TRUTHFIT_RATE_LIMIT_BACKEND must be one of: {supported}.")
    return backend


def retention_days(status: str = "completed") -> int:
    variable = {
        "pending": "TRUTHFIT_PENDING_RETENTION_DAYS",
        "processing": "TRUTHFIT_PENDING_RETENTION_DAYS",
        "failed": "TRUTHFIT_FAILED_RETENTION_DAYS",
        "completed": "TRUTHFIT_RETENTION_DAYS",
    }.get(status, "TRUTHFIT_RETENTION_DAYS")
    default = {"pending": 1, "processing": 1, "failed": 7}.get(status, 30)
    raw_value = (os.getenv(variable) or str(default)).strip()
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise RuntimeError(f"{variable} must be a positive integer.") from exc
    if value < 1 or value > 3650:
        raise RuntimeError(f"{variable} must be between 1 and 3650 days.")
    return value


def retention_cleanup_enabled() -> bool:
    return (os.getenv("TRUTHFIT_CLEANUP_ENABLED") or "true").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def retention_encryption_key() -> str:
    return (os.getenv("TRUTHFIT_RETENTION_ENCRYPTION_KEY") or "").strip()


def max_upload_bytes() -> int:
    return _bounded_int("TRUTHFIT_MAX_UPLOAD_BYTES", 5 * 1024 * 1024, 1024, 25 * 1024 * 1024)


def max_request_bytes() -> int:
    minimum = max_upload_bytes() + 1024
    default = max(12 * 1024 * 1024, minimum)
    return _bounded_int("TRUTHFIT_MAX_REQUEST_BYTES", default, minimum, 30 * 1024 * 1024)


def request_timeout_seconds() -> int:
    return _bounded_int("TRUTHFIT_REQUEST_TIMEOUT_SECONDS", 60, 5, 300)


def rate_limit_window_seconds() -> int:
    return _bounded_int("TRUTHFIT_RATE_LIMIT_WINDOW_SECONDS", 60, 1, 3600)


def general_rate_limit() -> int:
    return _bounded_int("TRUTHFIT_RATE_LIMIT_REQUESTS", 120, 1, 10_000)


def analysis_rate_limit() -> int:
    return _bounded_int("TRUTHFIT_ANALYSIS_RATE_LIMIT_REQUESTS", 10, 1, 1000)


def daily_analysis_quota() -> int:
    default = 5 if runtime_environment() == "production" else 100
    return _bounded_int("TRUTHFIT_DAILY_ANALYSIS_QUOTA", default, 1, 1000)


def max_page_size() -> int:
    return _bounded_int("TRUTHFIT_MAX_PAGE_SIZE", 100, 1, 500)


def trusted_hosts() -> list[str]:
    raw_hosts = (os.getenv("TRUTHFIT_TRUSTED_HOSTS") or "").strip()
    if not raw_hosts:
        if runtime_environment() == "production":
            raise RuntimeError("TRUTHFIT_TRUSTED_HOSTS is required when TRUTHFIT_ENV=production.")
        return list(DEVELOPMENT_TRUSTED_HOSTS)

    hosts = [_validate_host(value) for value in raw_hosts.split(",") if value.strip()]
    if not hosts:
        raise RuntimeError("TRUTHFIT_TRUSTED_HOSTS must include at least one hostname.")
    return list(dict.fromkeys(hosts))


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


def _validate_host(value: str) -> str:
    host = value.strip().lower()
    if not host or "://" in host or "/" in host or "@" in host or host == "*":
        raise RuntimeError(f"Invalid trusted host: {value.strip()}")
    if host.startswith("*."):
        suffix = host[2:]
        if not suffix or "." not in suffix:
            raise RuntimeError(f"Invalid trusted host: {value.strip()}")
        return host
    parsed = urlsplit(f"//{host}")
    if not parsed.hostname or parsed.path or parsed.query or parsed.fragment:
        raise RuntimeError(f"Invalid trusted host: {value.strip()}")
    try:
        port = parsed.port
    except ValueError as exc:
        raise RuntimeError(f"Invalid trusted host: {value.strip()}") from exc
    if port is not None:
        raise RuntimeError("TRUTHFIT_TRUSTED_HOSTS entries must not include ports.")
    return host


def _bounded_int(variable: str, default: int, minimum: int, maximum: int) -> int:
    raw_value = (os.getenv(variable) or str(default)).strip()
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise RuntimeError(f"{variable} must be an integer.") from exc
    if value < minimum or value > maximum:
        raise RuntimeError(f"{variable} must be between {minimum} and {maximum}.")
    return value
