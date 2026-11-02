from fastapi import APIRouter, Depends, File, Form, Request, UploadFile

from apps.api.app.auth import CurrentUser, get_current_user

from apps.api.app.schemas import (
    AnalysisRunRequest,
    AnalysisRunResponse,
    AnalysisListResponse,
    DashboardSummaryResponse,
    HealthResponse,
    JobParseResponse,
    ProvidersResponse,
    ResumeParseResponse,
    StoredAnalysisResponse,
    TailorRequest,
    TailorResponse,
    TrackerItem,
    TrackerResponse,
    TrackerUpdateRequest,
)
from apps.api.app.db.database import check_database
from apps.api.app.services.analysis_service import (
    get_analysis_run,
    list_analysis_runs,
    dashboard_summary,
    list_providers,
    list_tracked_jobs,
    run_analysis,
    tailor_resume,
    update_tracked_job,
)
from apps.api.app.services.parse_service import parse_job_description, parse_resume

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    database_status = "ok" if check_database() else "unavailable"
    return HealthResponse(status="ok", service="truthfit-api", database=database_status)


@router.post("/resumes/parse", response_model=ResumeParseResponse, tags=["resumes"])
async def parse_resume_endpoint(
    request: Request,
    file: UploadFile = File(...),
    _current_user: CurrentUser = Depends(get_current_user),
) -> ResumeParseResponse:
    return await parse_resume(file=file, request_id=request.state.request_id)


@router.post("/jobs/parse", response_model=JobParseResponse, tags=["jobs"])
async def parse_job_endpoint(
    request: Request,
    file: UploadFile | None = File(None),
    pasted_text: str = Form(""),
    job_link: str = Form(""),
    _current_user: CurrentUser = Depends(get_current_user),
) -> JobParseResponse:
    return await parse_job_description(
        file=file,
        pasted_text=pasted_text,
        job_link=job_link,
        request_id=request.state.request_id,
    )


@router.post("/analysis/run", response_model=AnalysisRunResponse, tags=["analysis"])
def run_analysis_endpoint(
    request: Request,
    payload: AnalysisRunRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> AnalysisRunResponse:
    return run_analysis(
        payload=payload,
        request_id=request.state.request_id,
        current_user=current_user,
    )


@router.get("/analysis", response_model=AnalysisListResponse, tags=["analysis"])
def list_analysis_endpoint(
    limit: int = 20,
    current_user: CurrentUser = Depends(get_current_user),
) -> AnalysisListResponse:
    return list_analysis_runs(current_user=current_user, limit=limit)


@router.get("/analysis/{run_id}", response_model=StoredAnalysisResponse, tags=["analysis"])
def get_analysis_endpoint(
    run_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> StoredAnalysisResponse:
    return get_analysis_run(run_id, current_user)


@router.post("/tailor", response_model=TailorResponse, tags=["tailoring"])
def tailor_endpoint(
    request: Request,
    payload: TailorRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> TailorResponse:
    return tailor_resume(
        payload=payload,
        request_id=request.state.request_id,
        current_user=current_user,
    )


@router.get("/providers", response_model=ProvidersResponse, tags=["providers"])
def providers_endpoint() -> ProvidersResponse:
    return list_providers()


@router.get("/dashboard/summary", response_model=DashboardSummaryResponse, tags=["dashboard"])
def dashboard_summary_endpoint(
    current_user: CurrentUser = Depends(get_current_user),
) -> DashboardSummaryResponse:
    return dashboard_summary(current_user)


@router.get("/tracker", response_model=TrackerResponse, tags=["tracker"])
def tracker_endpoint(
    current_user: CurrentUser = Depends(get_current_user),
) -> TrackerResponse:
    return list_tracked_jobs(current_user)


@router.post("/tracker/{run_id}", response_model=TrackerItem, tags=["tracker"])
def update_tracker_endpoint(
    run_id: str,
    payload: TrackerUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> TrackerItem:
    return update_tracked_job(run_id=run_id, payload=payload, current_user=current_user)
