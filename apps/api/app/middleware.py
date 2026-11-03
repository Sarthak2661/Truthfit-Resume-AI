import asyncio
import hashlib
import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import Request
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from redis.exceptions import RedisError
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from apps.api.app.config import (
    analysis_rate_limit,
    general_rate_limit,
    max_request_bytes,
    max_upload_bytes,
    rate_limit_window_seconds,
    rate_limit_backend,
    redis_url,
    request_timeout_seconds,
    runtime_environment,
)
from source.services.observability import new_request_id


class RequestBodyLimitMiddleware:
    def __init__(self, app, max_bytes: int | None = None):
        self.app = app
        self.max_bytes = max_bytes or max_request_bytes()
        self.upload_route_bytes = max_upload_bytes() + (512 * 1024)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_limit = (
            min(self.max_bytes, self.upload_route_bytes)
            if scope.get("path") in {"/resumes/parse", "/jobs/parse"}
            else self.max_bytes
        )
        headers = dict(scope.get("headers") or [])
        raw_length = headers.get(b"content-length", b"").decode("ascii", errors="ignore")
        if raw_length.isdigit() and int(raw_length) > request_limit:
            await _send_json_error(scope, receive, send, 413, "Request body is too large.")
            return

        received = 0

        async def limited_receive():
            nonlocal received
            message = await receive()
            if message.get("type") == "http.request":
                received += len(message.get("body", b""))
                if received > request_limit:
                    raise RequestBodyTooLarge
            return message

        try:
            await self.app(scope, limited_receive, send)
        except RequestBodyTooLarge:
            await _send_json_error(scope, receive, send, 413, "Request body is too large.")


class RequestTimeoutMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, timeout_seconds: int | None = None):
        super().__init__(app)
        self.timeout_seconds = timeout_seconds or request_timeout_seconds()

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        try:
            return await asyncio.wait_for(call_next(request), timeout=self.timeout_seconds)
        except TimeoutError:
            request_id = getattr(request.state, "request_id", new_request_id())
            return JSONResponse(
                status_code=504,
                content={"request_id": request_id, "detail": "Request timed out."},
                headers={"x-request-id": request_id},
            )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers["x-content-type-options"] = "nosniff"
        response.headers["x-frame-options"] = "DENY"
        response.headers["referrer-policy"] = "no-referrer"
        response.headers["permissions-policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["cache-control"] = "no-store"
        if runtime_environment() == "production":
            response.headers["strict-transport-security"] = "max-age=31536000; includeSubDomains"
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        window_seconds: int | None = None,
        default_limit: int | None = None,
        analysis_limit: int | None = None,
    ):
        super().__init__(app)
        self.window_seconds = window_seconds or rate_limit_window_seconds()
        self.default_limit = default_limit or general_rate_limit()
        self.analysis_limit = analysis_limit or analysis_rate_limit()
        self.backend = rate_limit_backend()
        self._redis = Redis.from_url(redis_url(), decode_responses=True) if self.backend == "redis" else None
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path == "/health":
            return await call_next(request)

        group = "analysis" if request.url.path in {"/analysis/run", "/tailor"} else "general"
        limit = self.analysis_limit if group == "analysis" else self.default_limit
        key = f"{group}:{_request_identity(request)}"
        try:
            count, retry_after = await self._consume(key)
        except RedisError:
            return JSONResponse(
                status_code=503,
                content={"detail": "Rate limit service is unavailable."},
            )

        if count > limit:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Retry later."},
                headers={"retry-after": str(retry_after)},
            )

        response = await call_next(request)
        response.headers["x-ratelimit-limit"] = str(limit)
        response.headers["x-ratelimit-remaining"] = str(max(0, limit - count))
        return response

    async def _consume(self, key: str) -> tuple[int, int]:
        if self._redis is not None:
            window = int(time.time() // self.window_seconds)
            redis_key = f"truthfit:rate:{key}:{window}"
            pipeline = self._redis.pipeline(transaction=True)
            pipeline.incr(redis_key)
            pipeline.expire(redis_key, self.window_seconds, nx=True)
            pipeline.ttl(redis_key)
            count, _, ttl = await pipeline.execute()
            return int(count), max(1, int(ttl))

        now = time.monotonic()
        with self._lock:
            bucket = self._requests[key]
            cutoff = now - self.window_seconds
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            bucket.append(now)
            retry_after = max(1, int(self.window_seconds - (now - bucket[0])) + 1)
            if len(self._requests) > 10_000:
                self._requests = defaultdict(deque, {
                    bucket_key: values
                    for bucket_key, values in self._requests.items()
                    if values and values[-1] > cutoff
                })
            return len(bucket), retry_after


class RequestBodyTooLarge(Exception):
    pass


def _request_identity(request: Request) -> str:
    authorization = request.headers.get("authorization", "")
    if authorization:
        return hashlib.sha256(authorization.encode("utf-8")).hexdigest()[:24]
    return request.client.host if request.client else "unknown"


async def _send_json_error(scope, receive, send, status_code: int, detail: str) -> None:
    response = JSONResponse(status_code=status_code, content={"detail": detail})
    await response(scope, receive, send)
