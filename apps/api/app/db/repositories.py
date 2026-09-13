from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.db.models import AgentEvent, AnalysisRun, Evidence, Job, Resume, User

ANONYMOUS_EMAIL = "anonymous@truthfit.local"


def get_or_create_user(session: Session, email: str | None = None) -> User:
    clean_email = (email or ANONYMOUS_EMAIL).strip().lower() or ANONYMOUS_EMAIL
    user = session.scalar(select(User).where(User.email == clean_email))

    if user:
        return user

    user = User(email=clean_email)
    session.add(user)
    session.flush()
    return user


def create_resume(
    session: Session,
    user_id: str,
    file_name: str,
    parsed_text: str,
    redacted_text: str,
) -> Resume:
    resume = Resume(
        user_id=user_id,
        file_name=file_name,
        parsed_text=parsed_text,
        redacted_text=redacted_text,
    )
    session.add(resume)
    session.flush()
    return resume


def create_job(
    session: Session,
    user_id: str,
    title: str,
    company: str,
    description: str,
) -> Job:
    job = Job(
        user_id=user_id,
        title=title,
        company=company,
        description=description,
    )
    session.add(job)
    session.flush()
    return job


def create_analysis_run(
    session: Session,
    user_id: str,
    resume_id: str,
    job_id: str,
    provider: str,
    model: str,
) -> AnalysisRun:
    run = AnalysisRun(
        user_id=user_id,
        resume_id=resume_id,
        job_id=job_id,
        status="running",
        provider=provider,
        model=model,
    )
    session.add(run)
    session.flush()
    return run


def complete_analysis_run(session: Session, run: AnalysisRun, analysis: dict) -> AnalysisRun:
    run.status = "completed"
    run.overall_score = int(analysis.get("scores", {}).get("overall_match_score") or 0)
    run.result_json = analysis
    run.completed_at = datetime.now(timezone.utc)
    session.flush()
    return run


def fail_analysis_run(session: Session, run: AnalysisRun, error_type: str) -> AnalysisRun:
    run.status = "failed"
    run.completed_at = datetime.now(timezone.utc)
    add_agent_event(
        session=session,
        analysis_run_id=run.id,
        agent_name="analysis",
        status="failed",
        error_type=error_type,
    )
    session.flush()
    return run


def add_evidence_records(session: Session, analysis_run_id: str, analysis: dict) -> list[Evidence]:
    records = []

    for item in analysis.get("confidence_findings", []):
        if not isinstance(item, dict):
            continue
        records.append(
            Evidence(
                analysis_run_id=analysis_run_id,
                requirement=str(item.get("finding") or item.get("requirement") or ""),
                resume_evidence=str(item.get("resume_evidence") or item.get("evidence") or ""),
                evidence_type=str(item.get("evidence_type") or "confidence_finding"),
                confidence=str(item.get("confidence") or "unknown"),
                verified=str(item.get("risk") or "").lower() in {"low", "verified", "supported"},
            )
        )

    for item in analysis.get("evidence_based_matches", []):
        if not isinstance(item, dict):
            continue
        records.append(
            Evidence(
                analysis_run_id=analysis_run_id,
                requirement=str(item.get("requirement") or item.get("finding") or ""),
                resume_evidence=str(item.get("resume_evidence") or item.get("evidence") or ""),
                evidence_type=str(item.get("evidence_type") or "requirement_match"),
                confidence=str(item.get("confidence") or item.get("evidence_status") or "unknown"),
                verified=str(item.get("evidence_status") or "").lower() in {"strong", "supported", "covered"},
            )
        )

    session.add_all(records)
    session.flush()
    return records


def add_agent_event(
    session: Session,
    analysis_run_id: str,
    agent_name: str,
    status: str,
    latency_ms: int = 0,
    error_type: str = "",
) -> AgentEvent:
    event = AgentEvent(
        analysis_run_id=analysis_run_id,
        agent_name=agent_name,
        status=status,
        latency_ms=latency_ms,
        error_type=error_type,
    )
    session.add(event)
    session.flush()
    return event


def get_analysis_run(session: Session, run_id: str) -> AnalysisRun | None:
    return session.get(AnalysisRun, run_id)
