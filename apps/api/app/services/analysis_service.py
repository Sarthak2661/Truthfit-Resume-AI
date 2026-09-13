from apps.api.app.db.database import session_scope
from apps.api.app.db import repositories
from apps.api.app.schemas import (
    AnalysisRunRequest,
    AnalysisRunResponse,
    ProviderInfo,
    ProvidersResponse,
    StoredAnalysisResponse,
    TailorRequest,
    TailorResponse,
)
from source.ai.llm_client import generate_resume_analysis
from source.ai.providers import PROVIDER_MODELS
from source.ai.schemas import validate_analysis_result
from source.services.evidence_score import add_resume_evidence_score
from source.services.observability import timed_operation
from source.services.resume_heatmap import redact_personal_details
from source.services.url_utils import normalize_http_url
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
                    job_description=payload.job_description,
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
