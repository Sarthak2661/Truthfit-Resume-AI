from datetime import datetime, timezone
from collections import Counter

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from apps.api.app.db.models import AgentEvent, AnalysisRun, Evidence, Job, Resume, User


def get_or_create_user(session: Session, auth_subject: str, email: str = "") -> User:
    clean_subject = auth_subject.strip()
    if not clean_subject:
        raise ValueError("Authenticated user subject is required.")

    user = session.scalar(select(User).where(User.auth_subject == clean_subject))

    if user:
        clean_email = email.strip().lower()
        if clean_email and user.email != clean_email:
            user.email = clean_email
            session.flush()
        return user

    user = User(auth_subject=clean_subject, email=email.strip().lower())
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


def get_analysis_run(session: Session, run_id: str, user_id: str) -> AnalysisRun | None:
    return session.scalar(
        select(AnalysisRun).where(
            AnalysisRun.id == run_id,
            AnalysisRun.user_id == user_id,
        )
    )


def update_tracker_status(
    session: Session,
    run: AnalysisRun,
    status: str,
    notes: str = "",
    priority: str | None = None,
    applied_at: str | None = None,
    follow_up_date: str | None = None,
) -> AnalysisRun:
    result = dict(run.result_json or {})
    current_tracker = dict(result.get("tracker") or {})
    now = datetime.now(timezone.utc)
    resolved_applied_at = applied_at if applied_at is not None else str(current_tracker.get("applied_at") or "")
    if status == "Applied" and not resolved_applied_at:
        resolved_applied_at = now.date().isoformat()
    result["tracker"] = {
        **current_tracker,
        "status": status,
        "notes": notes if notes or "notes" not in current_tracker else current_tracker.get("notes", ""),
        "priority": priority if priority is not None else str(current_tracker.get("priority") or "Normal"),
        "applied_at": resolved_applied_at,
        "follow_up_date": follow_up_date if follow_up_date is not None else str(current_tracker.get("follow_up_date") or ""),
        "updated_at": now.isoformat(),
        "saved": True,
    }
    run.result_json = result
    session.flush()
    return run


def list_analysis_runs(session: Session, user_id: str, limit: int = 20) -> list[AnalysisRun]:
    statement = (
        select(AnalysisRun)
        .where(AnalysisRun.user_id == user_id)
        .order_by(AnalysisRun.created_at.desc())
        .limit(limit)
    )
    return list(session.scalars(statement))


def analysis_counts(session: Session, user_id: str) -> dict[str, int]:
    total = (
        session.scalar(
            select(func.count()).select_from(AnalysisRun).where(AnalysisRun.user_id == user_id)
        )
        or 0
    )
    completed = (
        session.scalar(
            select(func.count()).select_from(AnalysisRun).where(
                AnalysisRun.user_id == user_id,
                AnalysisRun.status == "completed",
            )
        )
        or 0
    )
    failed = (
        session.scalar(
            select(func.count()).select_from(AnalysisRun).where(
                AnalysisRun.user_id == user_id,
                AnalysisRun.status == "failed",
            )
        )
        or 0
    )
    return {"total": total, "completed": completed, "failed": failed}


def average_completed_score(session: Session, user_id: str) -> float:
    value = session.scalar(
        select(func.avg(AnalysisRun.overall_score)).where(
            AnalysisRun.user_id == user_id,
            AnalysisRun.status == "completed",
        )
    )
    return round(float(value or 0), 1)


def provider_usage(session: Session, user_id: str) -> list[dict]:
    rows = session.execute(
        select(AnalysisRun.provider, func.count())
        .where(AnalysisRun.user_id == user_id)
        .group_by(AnalysisRun.provider)
        .order_by(func.count().desc())
    )
    return [{"provider": provider, "runs": count} for provider, count in rows]


def common_skill_gaps(session: Session, user_id: str, limit: int = 8) -> list[dict]:
    gaps = Counter()

    for run in session.scalars(
        select(AnalysisRun).where(
            AnalysisRun.user_id == user_id,
            AnalysisRun.status == "completed",
        )
    ):
        missing_skills = run.result_json.get("skills_analysis", {}).get("missing_skills", [])
        for item in missing_skills:
            if isinstance(item, dict):
                skill = str(item.get("skill") or item.get("requirement") or "").strip()
            else:
                skill = str(item).strip()
            if skill:
                gaps[skill] += 1

    return [{"skill": skill, "count": count} for skill, count in gaps.most_common(limit)]
