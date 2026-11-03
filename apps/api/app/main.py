from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from apps.api.app.routes import router
from apps.api.app.config import allowed_cors_origins, trusted_hosts
from apps.api.app.db.database import init_db
from apps.api.app.errors import (
    AnalysisQuotaExceededError,
    ResourceNotFoundError,
    UploadTooLargeError,
)
from apps.api.app.middleware import (
    RateLimitMiddleware,
    RequestBodyLimitMiddleware,
    RequestTimeoutMiddleware,
    SecurityHeadersMiddleware,
)
from apps.api.app.schemas import ErrorResponse
from source.services.observability import log_event, log_warning, new_request_id


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="TruthFit Resume AI API",
        description=(
            "API-first backend for parsing resumes, parsing job descriptions, "
            "running evidence-based resume analysis, tailoring resume content, "
            "and listing available LLM providers."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts())
    app.add_middleware(RequestTimeoutMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestBodyLimitMiddleware)

    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request_id = request.headers.get("x-request-id") or new_request_id()
        request.state.request_id = request_id
        log_event("api_request_started", request_id=request_id)

        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        log_event("api_request_completed", request_id=request_id, status=response.status_code)
        return response

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        request_id = getattr(request.state, "request_id", new_request_id())
        log_warning("api_validation_failed", request_id=request_id, error_type=exc.__class__.__name__)
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(request_id=request_id, detail=str(exc)).model_dump(),
            headers={"x-request-id": request_id},
        )

    @app.exception_handler(UploadTooLargeError)
    async def upload_too_large_handler(request: Request, exc: UploadTooLargeError):
        request_id = getattr(request.state, "request_id", new_request_id())
        return JSONResponse(
            status_code=413,
            content=ErrorResponse(request_id=request_id, detail=str(exc)).model_dump(),
            headers={"x-request-id": request_id},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        request_id = getattr(request.state, "request_id", new_request_id())
        log_warning("api_validation_failed", request_id=request_id, error_type=exc.__class__.__name__)
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(request_id=request_id, detail="Request validation failed.").model_dump(),
            headers={"x-request-id": request_id},
        )

    @app.exception_handler(ResourceNotFoundError)
    async def not_found_error_handler(request: Request, exc: ResourceNotFoundError):
        request_id = getattr(request.state, "request_id", new_request_id())
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(request_id=request_id, detail=str(exc)).model_dump(),
            headers={"x-request-id": request_id},
        )

    @app.exception_handler(AnalysisQuotaExceededError)
    async def analysis_quota_handler(request: Request, exc: AnalysisQuotaExceededError):
        request_id = getattr(request.state, "request_id", new_request_id())
        log_warning(
            "analysis_quota_exceeded",
            request_id=request_id,
            quota_limit=exc.limit,
            quota_used=exc.used,
        )
        return JSONResponse(
            status_code=429,
            content=ErrorResponse(request_id=request_id, detail=str(exc)).model_dump(),
            headers={
                "x-request-id": request_id,
                "retry-after": str(exc.retry_after_seconds),
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", new_request_id())
        log_warning("api_request_failed", request_id=request_id, error_type=exc.__class__.__name__)
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(request_id=request_id, detail="TruthFit could not complete the request.").model_dump(),
            headers={"x-request-id": request_id},
        )

    app.include_router(router)
    return app


app = create_app()
