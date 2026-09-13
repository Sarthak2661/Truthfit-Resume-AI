from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from apps.api.app.routes import router
from apps.api.app.db.database import init_db
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

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        request_id = getattr(request.state, "request_id", new_request_id())
        log_warning("api_validation_failed", request_id=request_id, error_type=exc.__class__.__name__)
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(request_id=request_id, detail="Request validation failed.").model_dump(),
            headers={"x-request-id": request_id},
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
