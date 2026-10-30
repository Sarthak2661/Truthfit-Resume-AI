from apps.api.app.db.database import session_scope
from apps.api.app.db import repositories
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
from source.ai.providers import PROVIDER_MODELS
from source.ai.schemas import validate_analysis_result
from source.services.evidence_score import add_resume_evidence_score
from source.services.observability import timed_operation
from source.services.resume_heatmap import redact_personal_details
from source.services.url_utils import is_valid_http_url, normalize_http_url
from source.ui.text_cleanup import normalize_analysis_result


def run_analysis(payload: AnalysisRunRequest, request_id: str) -> AnalysisRunResponse:
    provider = payload.provider
    model = payload.model or PROVIDER_MODELS[provider][0]
    redacted_resume = redact_personal_details(payload.resume_text)

    with session_scope() as session:
        user = repositories.get_or_create_user(session, payload.user_email)
        resume = repositories.create_resume(
            session=session,
            user_id=user.id,
            file_name=payload.resume_file_name,
            parsed_text=payload.resume_text,
            redacted_text=redacted_resume,
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

        try:
            with timed_operation("api_analysis_run", request_id=request_id, provider=provider, model=model):
                analysis = generate_resume_analysis(
                    resume_text=redacted_resume,
                    job_description=_regional_job_context(payload.job_description, payload.target_region),
                    include_cover_letter=payload.include_cover_letter,
                    user_projects=payload.user_projects,
                    provider=provider,
                    model=model,
                    api_key=payload.api_key,
                )
        except Exception as exc:
            repositories.fail_analysis_run(session, run, exc.__class__.__name__)
            raise

        normalized = _finalize_analysis(analysis, payload.job_link)
        if payload.resume_formatting_checks:
            normalized["ats_formatting_checks"] = payload.resume_formatting_checks
        normalized.setdefault("job_details", {})["target_region"] = payload.target_region
        repositories.complete_analysis_run(session, run, normalized)
        repositories.add_evidence_records(session, run.id, normalized)
        repositories.add_agent_event(
            session=session,
            analysis_run_id=run.id,
            agent_name="analysis",
            status="completed",
        )

        return AnalysisRunResponse(request_id=request_id, run_id=run.id, analysis=normalized)


def get_analysis_run(run_id: str) -> StoredAnalysisResponse:
    with session_scope() as session:
        run = repositories.get_analysis_run(session, run_id)
        if run is None:
            raise ValueError(f"Analysis run not found: {run_id}")

        return StoredAnalysisResponse(
            run_id=run.id,
            status=run.status,
            provider=run.provider,
            model=run.model,
            overall_score=run.overall_score,
            analysis=run.result_json,
        )


def list_analysis_runs(limit: int = 20) -> AnalysisListResponse:
    with session_scope() as session:
        runs = repositories.list_analysis_runs(session, limit=limit)
        return AnalysisListResponse(analyses=[_analysis_list_item(run) for run in runs])


def dashboard_summary() -> DashboardSummaryResponse:
    with session_scope() as session:
        counts = repositories.analysis_counts(session)
        recent_runs = repositories.list_analysis_runs(session, limit=8)

        return DashboardSummaryResponse(
            total_runs=counts["total"],
            completed_runs=counts["completed"],
            failed_runs=counts["failed"],
            average_match_score=repositories.average_completed_score(session),
            common_skill_gaps=repositories.common_skill_gaps(session),
            provider_usage=repositories.provider_usage(session),
            recent_analyses=[_analysis_list_item(run) for run in recent_runs],
        )


def list_tracked_jobs() -> TrackerResponse:
    with session_scope() as session:
        runs = repositories.list_analysis_runs(session, limit=100)
        jobs = [_tracker_item(run) for run in runs if _tracker_status(run) != "Not saved"]
        return TrackerResponse(jobs=jobs)


def update_tracked_job(run_id: str, payload: TrackerUpdateRequest) -> TrackerItem:
    with session_scope() as session:
        run = repositories.get_analysis_run(session, run_id)
        if run is None:
            raise ValueError(f"Analysis run not found: {run_id}")
        repositories.update_tracker_status(session, run, payload.status, payload.notes)
        return _tracker_item(run)


def tailor_resume(payload: TailorRequest, request_id: str) -> TailorResponse:
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
        analysis = run_analysis(analysis_payload, request_id).analysis

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
        created_at=run.created_at.isoformat(),
        completed_at=run.completed_at.isoformat() if run.completed_at else None,
    )
