from fastapi import APIRouter, File, Form, Request, UploadFile

from apps.api.app.schemas import (
    AnalysisRunRequest,
    AnalysisRunResponse,
    HealthResponse,
    JobParseResponse,
    ProvidersResponse,
    ResumeParseResponse,
    StoredAnalysisResponse,
    TailorRequest,
    TailorResponse,
)
from apps.api.app.db.database import check_database
from apps.api.app.services.analysis_service import (
    get_analysis_run,
    list_providers,
    run_analysis,
    tailor_resume,
)
from apps.api.app.services.parse_service import parse_job_description, parse_resume

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    database_status = "ok" if check_database() else "unavailable"
    return HealthResponse(status="ok", service="truthfit-api", database=database_status)


@router.post("/resumes/parse", response_model=ResumeParseResponse, tags=["resumes"])
async def parse_resume_endpoint(request: Request, file: UploadFile = File(...)) -> ResumeParseResponse:
    return await parse_resume(file=file, request_id=request.state.request_id)


@router.post("/jobs/parse", response_model=JobParseResponse, tags=["jobs"])
async def parse_job_endpoint(
    request: Request,
    file: UploadFile | None = File(None),
    pasted_text: str = Form(""),
    job_link: str = Form(""),
) -> JobParseResponse:
    return await parse_job_description(
        file=file,
        pasted_text=pasted_text,
        job_link=job_link,
        request_id=request.state.request_id,
    )


@router.post("/analysis/run", response_model=AnalysisRunResponse, tags=["analysis"])
def run_analysis_endpoint(request: Request, payload: AnalysisRunRequest) -> AnalysisRunResponse:
    return run_analysis(payload=payload, request_id=request.state.request_id)


@router.get("/analysis/{run_id}", response_model=StoredAnalysisResponse, tags=["analysis"])
def get_analysis_endpoint(run_id: str) -> StoredAnalysisResponse:
    return get_analysis_run(run_id)


@router.post("/tailor", response_model=TailorResponse, tags=["tailoring"])
def tailor_endpoint(request: Request, payload: TailorRequest) -> TailorResponse:
    return tailor_resume(payload=payload, request_id=request.state.request_id)


@router.get("/providers", response_model=ProvidersResponse, tags=["providers"])
def providers_endpoint() -> ProvidersResponse:
    return list_providers()
