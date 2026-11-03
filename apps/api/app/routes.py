from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Header, HTTPException, Query, Request, UploadFile, status

from apps.api.app.auth import CurrentUser, get_current_user
from apps.api.app.analysis_queue import enqueue_analysis
from apps.api.app.config import analysis_queue_backend, max_page_size

from apps.api.app.schemas import (
    AnalysisRunRequest,
    AnalysisRunResponse,
    AnalysisListResponse,
    AccountDataResponse,
    DataDeletionResponse,
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
    create_pending_analysis,
    build_analysis_task_payload,
    fail_pending_analysis,
    tailor_resume,
    update_tracked_job,
)
from apps.api.app.services.parse_service import parse_job_description, parse_resume
from apps.api.app.services.privacy_service import (
    delete_account_data,
    delete_owned_analysis,
    inspect_account_data,
)

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


@router.post(
    "/analysis/run",
    response_model=AnalysisRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["analysis"],
)
def run_analysis_endpoint(
    request: Request,
    payload: AnalysisRunRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser = Depends(get_current_user),
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
        min_length=8,
        max_length=128,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]+$",
    ),
) -> AnalysisRunResponse:
    use_server_key = analysis_queue_backend() == "rq"
    if use_server_key and payload.api_key:
        raise HTTPException(
            status_code=400,
            detail="Public queued analysis uses server-managed provider credentials. Remove the BYOK key.",
        )
    accepted = create_pending_analysis(
        payload=payload,
        request_id=request.state.request_id,
        current_user=current_user,
        idempotency_key=idempotency_key,
    )
    if accepted.idempotent_replay:
        return accepted
    try:
        enqueue_analysis(
            background_tasks=background_tasks,
            run_id=accepted.run_id,
            payload=build_analysis_task_payload(payload, server_managed_key=use_server_key),
            request_id=request.state.request_id,
        )
    except Exception as exc:
        fail_pending_analysis(
            accepted.run_id,
            "The analysis queue is unavailable. Retry the run later.",
        )
        raise HTTPException(status_code=503, detail="The analysis queue is unavailable.") from exc
    return accepted


@router.delete("/analysis/{run_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["analysis"])
def delete_analysis_endpoint(
    run_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> None:
    delete_owned_analysis(run_id, current_user)


@router.get("/account/data", response_model=AccountDataResponse, tags=["privacy"])
def account_data_endpoint(
    current_user: CurrentUser = Depends(get_current_user),
) -> AccountDataResponse:
    return inspect_account_data(current_user)


@router.delete("/account/data", response_model=DataDeletionResponse, tags=["privacy"])
def delete_account_data_endpoint(
    current_user: CurrentUser = Depends(get_current_user),
) -> DataDeletionResponse:
    return delete_account_data(current_user)


@router.get("/analysis", response_model=AnalysisListResponse, tags=["analysis"])
def list_analysis_endpoint(
    limit: int = Query(default=20, ge=1, le=500),
    offset: int = Query(default=0, ge=0, le=1_000_000),
    current_user: CurrentUser = Depends(get_current_user),
) -> AnalysisListResponse:
    if limit > max_page_size():
        raise HTTPException(
            status_code=422,
            detail=f"limit must be no greater than {max_page_size()}.",
        )
    return list_analysis_runs(current_user=current_user, limit=limit, offset=offset)


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
