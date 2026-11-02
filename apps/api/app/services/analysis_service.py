from collections import defaultdict
from time import perf_counter

from apps.api.app.db.database import session_scope
from apps.api.app.db import repositories
from apps.api.app.auth import CurrentUser
from apps.api.app.errors import ResourceNotFoundError
from apps.api.app.schemas import (
    AnalysisListItem,
    AnalysisListResponse,
    AnalysisRunRequest,
    AnalysisRunResponse,
    DashboardSummaryResponse,
    ProviderInfo,
    ProvidersResponse,
    StoredAnalysisResponse,
    TailorRequest,
    TailorResponse,
    TrackerItem,
    TrackerResponse,
    TrackerUpdateRequest,
)
from source.ai.llm_client import generate_resume_analysis
from source.ai.errors import ProviderError, public_provider_message
from source.ai.providers import PROVIDER_MODELS
from source.ai.schemas import validate_analysis_result
from source.services.evidence_score import add_resume_evidence_score
from source.services.observability import log_warning, timed_operation
from source.services.resume_heatmap import redact_personal_details
from source.services.privacy_storage import encrypt_retained_text
from source.services.url_utils import is_valid_http_url, normalize_http_url
from source.ui.text_cleanup import normalize_analysis_result


def create_pending_analysis(
    payload: AnalysisRunRequest,
    request_id: str,
    current_user: CurrentUser,
) -> AnalysisRunResponse:
    provider = payload.provider
    model = payload.model or PROVIDER_MODELS[provider][0]
    redacted_resume = redact_personal_details(payload.resume_text)
    encrypted_original = None
    encryption_nonce = None
    if payload.retain_original_resume:
        encrypted_original, encryption_nonce = encrypt_retained_text(payload.resume_text)

    with session_scope() as session:
        user = repositories.get_or_create_user(
            session,
            auth_subject=current_user.subject,
            email=current_user.email,
        )
        resume = repositories.create_resume(
            session=session,
            user_id=user.id,
            file_name=payload.resume_file_name,
            redacted_text=redacted_resume,
            encrypted_original=encrypted_original,
            encryption_nonce=encryption_nonce,
        )

        job = repositories.create_job(
            session=session,
            user_id=user.id,
            title=payload.job_title,
            company=payload.company,
            description=payload.job_description,
        )

        run = repositories.create_analysis_run(
            session=session,
            user_id=user.id,
            resume_id=resume.id,
            job_id=job.id,
            provider=provider,
            model=model,
        )
        repositories.add_agent_event(
            session=session,
            analysis_run_id=run.id,
            agent_name="analysis",
            status="pending",
        )
        run_id = run.id

    return AnalysisRunResponse(
        request_id=request_id,
        run_id=run_id,
        status="pending",
        status_url=f"/analysis/{run_id}",
    )


def build_analysis_task_payload(payload: AnalysisRunRequest, server_managed_key: bool) -> dict:
    task_payload = payload.model_dump()
    task_payload["resume_text"] = redact_personal_details(payload.resume_text)
    task_payload["retain_original_resume"] = False
    if server_managed_key:
        task_payload["api_key"] = ""
    return task_payload


def process_analysis_run(run_id: str, payload_data: dict, request_id: str) -> None:
    payload = AnalysisRunRequest.model_validate(payload_data)
    started_at = perf_counter()

    with session_scope() as session:
        run = repositories.get_analysis_run_internal(session, run_id)
        if run is None or run.status not in {"pending", "processing"}:
            return
        repositories.mark_analysis_run_processing(session, run)
        repositories.add_agent_event(
            session=session,
            analysis_run_id=run.id,
            agent_name="analysis",
            status="processing",
        )

    try:
        with timed_operation(
            "api_analysis_run",
            request_id=request_id,
            provider=payload.provider,
            model=payload.model or PROVIDER_MODELS[payload.provider][0],
        ):
            analysis = generate_resume_analysis(
                resume_text=redact_personal_details(payload.resume_text),
                job_description=_regional_job_context(payload.job_description, payload.target_region),
                include_cover_letter=payload.include_cover_letter,
                user_projects=payload.user_projects,
                provider=payload.provider,
                model=payload.model or PROVIDER_MODELS[payload.provider][0],
                api_key=payload.api_key,
            )

        normalized = _finalize_analysis(analysis, payload.job_link)
        if payload.resume_formatting_checks:
            normalized["ats_formatting_checks"] = payload.resume_formatting_checks
        normalized.setdefault("job_details", {})["target_region"] = payload.target_region
        latency_ms = int((perf_counter() - started_at) * 1000)

        with session_scope() as session:
            run = repositories.get_analysis_run_internal(session, run_id)
            if run is None:
                return
            repositories.complete_analysis_run(session, run, normalized)
            repositories.add_evidence_records(session, run.id, normalized)
            repositories.add_agent_event(
                session=session,
                analysis_run_id=run.id,
                agent_name="analysis",
                status="completed",
                latency_ms=latency_ms,
            )
    except ProviderError as exc:
        _record_analysis_failure(run_id, exc.code, public_provider_message(exc), started_at)
        log_warning(
            "api_analysis_failed",
            request_id=request_id,
            run_id=run_id,
            provider=payload.provider,
            model=payload.model,
            error_type=exc.code,
        )
    except Exception as exc:
        _record_analysis_failure(
            run_id,
            "analysis_processing_error",
            "TruthFit could not complete this analysis. Retry the run.",
            started_at,
        )
        log_warning(
            "api_analysis_failed",
            request_id=request_id,
            run_id=run_id,
            provider=payload.provider,
            model=payload.model,
            error_type=exc.__class__.__name__,
        )


def _record_analysis_failure(
    run_id: str,
    error_type: str,
    error_message: str,
    started_at: float,
) -> None:
    with session_scope() as session:
        run = repositories.get_analysis_run_internal(session, run_id)
        if run is None:
            return
        repositories.fail_analysis_run(
            session,
            run,
            error_type,
            error_message,
            latency_ms=int((perf_counter() - started_at) * 1000),
        )


def fail_pending_analysis(run_id: str, error_message: str) -> None:
    _record_analysis_failure(
        run_id=run_id,
        error_type="analysis_queue_error",
        error_message=error_message,
        started_at=perf_counter(),
    )


def get_analysis_run(run_id: str, current_user: CurrentUser) -> StoredAnalysisResponse:
    with session_scope() as session:
        user = _resolve_user(session, current_user)
        run = repositories.get_analysis_run(session, run_id, user.id)
        if run is None:
            raise ResourceNotFoundError("Analysis run not found.")

        return StoredAnalysisResponse(
            run_id=run.id,
            status=run.status,
            provider=run.provider,
            model=run.model,
            overall_score=run.overall_score,
            analysis=run.result_json,
        )


def list_analysis_runs(current_user: CurrentUser, limit: int = 20) -> AnalysisListResponse:
    with session_scope() as session:
        user = _resolve_user(session, current_user)
        runs = repositories.list_analysis_runs(session, user.id, limit=limit)
        return AnalysisListResponse(analyses=[_analysis_list_item(run) for run in runs])


def dashboard_summary(current_user: CurrentUser) -> DashboardSummaryResponse:
    with session_scope() as session:
        user = _resolve_user(session, current_user)
        counts = repositories.analysis_counts(session, user.id)
        recent_runs = repositories.list_analysis_runs(session, user.id, limit=40)
        tracked_runs = [run for run in recent_runs if _tracker_status(run) != "Not saved"]

        return DashboardSummaryResponse(
            total_runs=counts["total"],
            completed_runs=counts["completed"],
            failed_runs=counts["failed"],
            average_match_score=repositories.average_completed_score(session, user.id),
            common_skill_gaps=repositories.common_skill_gaps(session, user.id),
            provider_usage=repositories.provider_usage(session, user.id),
            recent_analyses=[_analysis_list_item(run) for run in recent_runs[:8]],
            tracker_status_counts=_tracker_status_counts(tracked_runs),
            score_history=_score_history(recent_runs),
            resume_versions=_resume_versions(recent_runs),
            upcoming_actions=_upcoming_actions(tracked_runs),
        )


def list_tracked_jobs(current_user: CurrentUser) -> TrackerResponse:
    with session_scope() as session:
        user = _resolve_user(session, current_user)
        runs = repositories.list_analysis_runs(session, user.id, limit=100)
        jobs = [_tracker_item(run) for run in runs if _tracker_status(run) != "Not saved"]
        return TrackerResponse(jobs=jobs)


def update_tracked_job(
    run_id: str,
    payload: TrackerUpdateRequest,
    current_user: CurrentUser,
) -> TrackerItem:
    with session_scope() as session:
        user = _resolve_user(session, current_user)
        run = repositories.get_analysis_run(session, run_id, user.id)
        if run is None:
            raise ResourceNotFoundError("Analysis run not found.")
        repositories.update_tracker_status(
            session,
            run,
            payload.status,
            payload.notes,
            payload.priority,
            payload.applied_at,
            payload.follow_up_date,
        )
        return _tracker_item(run)


def tailor_resume(
    payload: TailorRequest,
    request_id: str,
    current_user: CurrentUser,
) -> TailorResponse:
    if payload.analysis:
        analysis = _finalize_analysis(payload.analysis)
    else:
        if not payload.resume_text.strip() or not payload.job_description.strip():
            raise ValueError("Provide either an analysis object or resume_text and job_description.")

        analysis_payload = AnalysisRunRequest(
            resume_text=payload.resume_text,
            job_description=payload.job_description,
            include_cover_letter=payload.include_cover_letter,
            user_projects=payload.user_projects,
            provider=payload.provider,
            model=payload.model,
            api_key=payload.api_key,
        )
        analysis = generate_resume_analysis(
            resume_text=redact_personal_details(analysis_payload.resume_text),
            job_description=_regional_job_context(
                analysis_payload.job_description,
                analysis_payload.target_region,
            ),
            include_cover_letter=analysis_payload.include_cover_letter,
            user_projects=analysis_payload.user_projects,
            provider=analysis_payload.provider,
            model=analysis_payload.model or PROVIDER_MODELS[analysis_payload.provider][0],
            api_key=analysis_payload.api_key,
        )
        analysis = _finalize_analysis(analysis)

    return TailorResponse(
        request_id=request_id,
        tailored_resume_content=analysis.get("tailored_resume_content", {}),
        before_after_bullets=analysis.get("before_after_bullets", []),
        resume_fix_suggestions=analysis.get("resume_fix_suggestions", []),
        cover_letter=analysis.get("cover_letter", ""),
    )


def list_providers() -> ProvidersResponse:
    return ProvidersResponse(
        providers=[
            ProviderInfo(name=name, models=models, default_model=models[0])
            for name, models in PROVIDER_MODELS.items()
        ]
    )


def _resolve_user(session, current_user: CurrentUser):
    return repositories.get_or_create_user(
        session,
        auth_subject=current_user.subject,
        email=current_user.email,
    )


def _finalize_analysis(analysis: dict, job_link: str = "") -> dict:
    normalized = normalize_analysis_result(validate_analysis_result(analysis))
    normalized = add_resume_evidence_score(normalized)

    if job_link:
        normalized.setdefault("job_details", {})["job_link"] = normalize_http_url(job_link)

    return normalized


def _regional_job_context(job_description: str, target_region: str) -> str:
    notes = {
        "US": "Target region: US. Consider US role titles, authorization language, location constraints, and common ATS keyword phrasing.",
        "India": "Target region: India. Consider India role titles, notice period context, city/hybrid requirements, and local hiring terminology.",
        "GCC": "Target region: GCC. Consider Gulf region relocation, visa sponsorship, regional domain expectations, and employer-location fit.",
        "Canada/Europe": "Target region: Canada/Europe. Treat this as a future/experimental targeting mode and call out uncertain regional assumptions.",
    }
    return f"{notes.get(target_region, notes['US'])}\n\n{job_description}"


def _tracker_item(run) -> TrackerItem:
    analysis = run.result_json or {}
    job_details = analysis.get("job_details", {}) if isinstance(analysis.get("job_details"), dict) else {}
    tracker = analysis.get("tracker", {}) if isinstance(analysis.get("tracker"), dict) else {}
    raw_job_link = str(job_details.get("job_link") or "").strip()
    job_link = raw_job_link if is_valid_http_url(raw_job_link) else ""
    return TrackerItem(
        run_id=run.id,
        role=(run.job.title if run.job else "") or job_details.get("job_title") or "Untitled role",
        company=(run.job.company if run.job else "") or job_details.get("company_name") or "Company not specified",
        location=str(job_details.get("location_or_work_policy") or ""),
        job_link=job_link,
        match_score=run.overall_score,
        tracker_status=_tracker_status(run),
        notes=str(tracker.get("notes") or ""),
        priority=str(tracker.get("priority") or "Normal"),
        applied_at=str(tracker.get("applied_at") or ""),
        follow_up_date=str(tracker.get("follow_up_date") or ""),
        updated_at=str(tracker.get("updated_at") or ""),
        top_fixes=_top_fixes(analysis),
        analysis_url=f"/analysis/{run.id}",
        created_at=run.created_at.isoformat(),
    )


def _tracker_status(run) -> str:
    tracker = (run.result_json or {}).get("tracker", {})
    if isinstance(tracker, dict):
        return str(tracker.get("status") or "Not saved")
    return "Not saved"


def _top_fixes(analysis: dict) -> list[str]:
    fixes = analysis.get("fix_impact_matrix", [])
    if not isinstance(fixes, list):
        return []

    top_fixes = []
    for item in fixes[:3]:
        if isinstance(item, dict):
            top_fixes.append(str(item.get("fix") or item.get("recommendation") or item.get("issue") or "Recommended fix"))
        else:
            top_fixes.append(str(item))
    return top_fixes


def _analysis_list_item(run) -> AnalysisListItem:
    return AnalysisListItem(
        run_id=run.id,
        status=run.status,
        provider=run.provider,
        model=run.model,
        overall_score=run.overall_score,
        job_title=run.job.title if run.job else "",
        company=run.job.company if run.job else "",
        resume_file_name=run.resume.file_name if run.resume else "",
        created_at=run.created_at.isoformat(),
        completed_at=run.completed_at.isoformat() if run.completed_at else None,
    )


def _tracker_status_counts(runs) -> dict[str, int]:
    counts = {"Saved": 0, "Applied": 0, "Interview": 0, "Rejected": 0}
    for run in runs:
        status = _tracker_status(run)
        if status in counts:
            counts[status] += 1
    return counts


def _score_history(runs) -> list[dict]:
    completed = [run for run in reversed(runs) if run.status == "completed"][-10:]
    return [
        {
            "run_id": run.id,
            "score": run.overall_score,
            "role": (run.job.title if run.job else "") or "Untitled role",
            "company": (run.job.company if run.job else "") or "Company not specified",
            "resume_file_name": run.resume.file_name if run.resume else "",
            "created_at": run.created_at.isoformat(),
        }
        for run in completed
    ]


def _resume_versions(runs) -> list[dict]:
    grouped = defaultdict(list)
    for run in reversed(runs):
        if run.status != "completed" or not run.resume:
            continue
        role = ((run.job.title if run.job else "") or "Untitled role").strip()
        company = ((run.job.company if run.job else "") or "Company not specified").strip()
        grouped[(role.casefold(), company.casefold())].append(run)

    versions = []
    for items in grouped.values():
        latest = items[-1]
        previous = items[-2] if len(items) > 1 else None
        role = (latest.job.title if latest.job else "") or "Untitled role"
        company = (latest.job.company if latest.job else "") or "Company not specified"
        latest_file_name = latest.resume.file_name or "Unnamed resume"
        versions.append(
            {
                "role": role,
                "company": company,
                "resume_file_name": latest_file_name,
                "latest_resume_file_name": latest_file_name,
                "previous_resume_file_name": previous.resume.file_name if previous and previous.resume else "",
                "runs": len(items),
                "latest_score": latest.overall_score,
                "best_score": max(item.overall_score for item in items),
                "change": latest.overall_score - previous.overall_score if previous is not None else None,
                "latest_run_id": latest.id,
            }
        )
    return sorted(versions, key=lambda item: (item["runs"], item["latest_score"]), reverse=True)[:6]


def _upcoming_actions(runs) -> list[dict]:
    actions = []
    for run in runs:
        tracker = (run.result_json or {}).get("tracker", {})
        if not isinstance(tracker, dict) or not tracker.get("follow_up_date"):
            continue
        actions.append(
            {
                "run_id": run.id,
                "role": (run.job.title if run.job else "") or "Untitled role",
                "company": (run.job.company if run.job else "") or "Company not specified",
                "follow_up_date": str(tracker.get("follow_up_date")),
                "status": _tracker_status(run),
            }
        )
    return sorted(actions, key=lambda item: item["follow_up_date"])[:6]
