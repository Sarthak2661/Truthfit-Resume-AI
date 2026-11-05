from datetime import date, datetime, timedelta, timezone
from uuid import uuid4
from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from apps.api.app.db.models import (
    AgentEvent,
    AnalysisRun,
    DailyAnalysisUsage,
    Evidence,
    Job,
    Resume,
    SkillGap,
    User,
)
from apps.api.app.config import retention_days


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
    try:
        with session.begin_nested():
            session.add(user)
            session.flush()
    except IntegrityError:
        user = session.scalar(select(User).where(User.auth_subject == clean_subject))
        if user is None:
            raise
    return user


def create_resume(
    session: Session,
    user_id: str,
    file_name: str,
    redacted_text: str,
    encrypted_original: str | None = None,
    encryption_nonce: str | None = None,
) -> Resume:
    resume = Resume(
        user_id=user_id,
        file_name=file_name,
        parsed_text=None,
        redacted_text=redacted_text,
        encrypted_original=encrypted_original,
        encryption_nonce=encryption_nonce,
        original_retained=bool(encrypted_original),
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
    idempotency_key: str | None = None,
    request_fingerprint: str | None = None,
    prompt_version: str = "v1",
    schema_version: str = "v1",
    consent_version: str | None = None,
    consented_at: datetime | None = None,
) -> AnalysisRun:
    run = AnalysisRun(
        user_id=user_id,
        resume_id=resume_id,
        job_id=job_id,
        status="pending",
        provider=provider,
        model=model,
        idempotency_key=idempotency_key,
        request_fingerprint=request_fingerprint,
        prompt_version=prompt_version,
        schema_version=schema_version,
        consent_version=consent_version,
        consented_at=consented_at,
        expires_at=datetime.now(timezone.utc) + timedelta(days=retention_days("pending")),
    )
    session.add(run)
    session.flush()
    return run


def consume_daily_analysis_quota(
    session: Session,
    user_id: str,
    usage_date: date,
    limit: int,
) -> int | None:
    """Atomically increment a user's daily usage, returning None at the limit."""
    values = {
        "id": uuid4().hex,
        "user_id": user_id,
        "usage_date": usage_date,
        "used_count": 1,
        "updated_at": datetime.now(timezone.utc),
    }
    dialect_name = session.get_bind().dialect.name
    if dialect_name == "postgresql":
        statement = postgresql_insert(DailyAnalysisUsage).values(**values)
    elif dialect_name == "sqlite":
        statement = sqlite_insert(DailyAnalysisUsage).values(**values)
    else:
        raise RuntimeError(f"Atomic quota enforcement is unsupported for {dialect_name}.")

    statement = statement.on_conflict_do_update(
        index_elements=["user_id", "usage_date"],
        set_={
            "used_count": DailyAnalysisUsage.used_count + 1,
            "updated_at": values["updated_at"],
        },
        where=DailyAnalysisUsage.used_count < limit,
    ).returning(DailyAnalysisUsage.used_count)
    return session.scalar(statement)


def daily_analysis_usage_count(session: Session, user_id: str, usage_date: date) -> int:
    return int(
        session.scalar(
            select(DailyAnalysisUsage.used_count).where(
                DailyAnalysisUsage.user_id == user_id,
                DailyAnalysisUsage.usage_date == usage_date,
            )
        )
        or 0
    )


def complete_analysis_run(session: Session, run: AnalysisRun, analysis: dict) -> AnalysisRun:
    run.status = "completed"
    run.overall_score = int(analysis.get("scores", {}).get("overall_match_score") or 0)
    run.result_json = analysis
    run.completed_at = datetime.now(timezone.utc)
    run.expires_at = run.completed_at + timedelta(days=retention_days("completed"))
    replace_skill_gap_records(session, run.id, run.user_id, analysis)
    session.flush()
    return run


def mark_analysis_run_processing(session: Session, run: AnalysisRun) -> AnalysisRun:
    run.status = "processing"
    session.flush()
    return run


def fail_analysis_run(
    session: Session,
    run: AnalysisRun,
    error_type: str,
    error_message: str,
    latency_ms: int = 0,
) -> AnalysisRun:
    run.status = "failed"
    run.result_json = {"error": {"type": error_type, "message": error_message}}
    run.completed_at = datetime.now(timezone.utc)
    run.expires_at = run.completed_at + timedelta(days=retention_days("failed"))
    add_agent_event(
        session=session,
        analysis_run_id=run.id,
        agent_name="analysis",
        status="failed",
        latency_ms=latency_ms,
        error_type=error_type,
    )
    session.flush()
    return run


def get_analysis_run_internal(session: Session, run_id: str) -> AnalysisRun | None:
    return session.scalar(select(AnalysisRun).where(AnalysisRun.id == run_id))


def get_analysis_run_by_idempotency_key(
    session: Session,
    user_id: str,
    idempotency_key: str,
) -> AnalysisRun | None:
    return session.scalar(
        select(AnalysisRun).where(
            AnalysisRun.user_id == user_id,
            AnalysisRun.idempotency_key == idempotency_key,
        )
    )


def count_analysis_runs_since(session: Session, user_id: str, since: datetime) -> int:
    return int(
        session.scalar(
            select(func.count())
            .select_from(AnalysisRun)
            .where(
                AnalysisRun.user_id == user_id,
                AnalysisRun.created_at >= since,
            )
        )
        or 0
    )


def account_data_summary(session: Session, user_id: str) -> dict:
    def count(model) -> int:
        return int(
            session.scalar(select(func.count()).select_from(model).where(model.user_id == user_id)) or 0
        )

    retained_originals = int(
        session.scalar(
            select(func.count())
            .select_from(Resume)
            .where(
                Resume.user_id == user_id,
                Resume.original_retained.is_(True),
            )
        )
        or 0
    )
    oldest = session.scalar(select(func.min(AnalysisRun.created_at)).where(AnalysisRun.user_id == user_id))
    return {
        "analyses": count(AnalysisRun),
        "resumes": count(Resume),
        "jobs": count(Job),
        "retained_originals": retained_originals,
        "oldest_record": oldest.isoformat() if oldest else None,
    }


def delete_analysis_run(session: Session, run: AnalysisRun) -> dict[str, int]:
    resume_id = run.resume_id
    job_id = run.job_id
    session.execute(delete(Evidence).where(Evidence.analysis_run_id == run.id))
    session.execute(delete(AgentEvent).where(AgentEvent.analysis_run_id == run.id))
    session.execute(delete(SkillGap).where(SkillGap.analysis_run_id == run.id))
    session.delete(run)
    session.flush()

    deleted_resumes = 0
    deleted_jobs = 0
    resume_references = session.scalar(
        select(func.count()).select_from(AnalysisRun).where(AnalysisRun.resume_id == resume_id)
    )
    if not resume_references:
        deleted_resumes = int(session.execute(delete(Resume).where(Resume.id == resume_id)).rowcount or 0)
    job_references = session.scalar(
        select(func.count()).select_from(AnalysisRun).where(AnalysisRun.job_id == job_id)
    )
    if not job_references:
        deleted_jobs = int(session.execute(delete(Job).where(Job.id == job_id)).rowcount or 0)
    session.flush()
    return {"analyses": 1, "resumes": deleted_resumes, "jobs": deleted_jobs}


def delete_user_data(session: Session, user: User) -> dict[str, int]:
    totals = {"analyses": 0, "resumes": 0, "jobs": 0}
    runs = list(session.scalars(select(AnalysisRun).where(AnalysisRun.user_id == user.id)))
    for run in runs:
        deleted = delete_analysis_run(session, run)
        for key in totals:
            totals[key] += deleted[key]

    totals["resumes"] += int(session.execute(delete(Resume).where(Resume.user_id == user.id)).rowcount or 0)
    totals["jobs"] += int(session.execute(delete(Job).where(Job.user_id == user.id)).rowcount or 0)
    session.execute(delete(DailyAnalysisUsage).where(DailyAnalysisUsage.user_id == user.id))
    session.delete(user)
    session.flush()
    return totals


def expired_analysis_runs(session: Session, now: datetime | None = None) -> list[AnalysisRun]:
    cutoff = now or datetime.now(timezone.utc)
    return list(session.scalars(select(AnalysisRun).where(AnalysisRun.expires_at <= cutoff)))


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
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    estimated_cost_micros: int | None = None,
) -> AgentEvent:
    event = AgentEvent(
        analysis_run_id=analysis_run_id,
        agent_name=agent_name,
        status=status,
        latency_ms=latency_ms,
        error_type=error_type,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        estimated_cost_micros=estimated_cost_micros,
    )
    session.add(event)
    session.flush()
    return event


def replace_skill_gap_records(
    session: Session,
    analysis_run_id: str,
    user_id: str,
    analysis: dict,
) -> list[SkillGap]:
    session.execute(delete(SkillGap).where(SkillGap.analysis_run_id == analysis_run_id))
    missing_skills = analysis.get("skills_analysis", {}).get("missing_skills", [])
    unique_skills: dict[str, str] = {}
    for item in missing_skills:
        raw_skill = item.get("skill") or item.get("requirement") if isinstance(item, dict) else item
        display_skill = " ".join(str(raw_skill or "").split())[:255]
        normalized_skill = display_skill.casefold()
        if normalized_skill:
            unique_skills.setdefault(normalized_skill, display_skill)

    records = [
        SkillGap(
            analysis_run_id=analysis_run_id,
            user_id=user_id,
            normalized_skill=normalized,
            display_skill=display,
        )
        for normalized, display in unique_skills.items()
    ]
    session.add_all(records)
    session.flush()
    return records


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
    resolved_applied_at = (
        applied_at if applied_at is not None else str(current_tracker.get("applied_at") or "")
    )
    if status == "Applied" and not resolved_applied_at:
        resolved_applied_at = now.date().isoformat()
    result["tracker"] = {
        **current_tracker,
        "status": status,
        "notes": notes if notes or "notes" not in current_tracker else current_tracker.get("notes", ""),
        "priority": priority if priority is not None else str(current_tracker.get("priority") or "Normal"),
        "applied_at": resolved_applied_at,
        "follow_up_date": follow_up_date
        if follow_up_date is not None
        else str(current_tracker.get("follow_up_date") or ""),
        "updated_at": now.isoformat(),
        "saved": True,
    }
    run.result_json = result
    session.flush()
    return run


def list_analysis_runs(
    session: Session,
    user_id: str,
    limit: int = 20,
    offset: int = 0,
) -> list[AnalysisRun]:
    statement = (
        select(AnalysisRun)
        .where(AnalysisRun.user_id == user_id)
        .order_by(AnalysisRun.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(session.scalars(statement))


def analysis_counts(session: Session, user_id: str) -> dict[str, int]:
    total = (
        session.scalar(select(func.count()).select_from(AnalysisRun).where(AnalysisRun.user_id == user_id))
        or 0
    )
    completed = (
        session.scalar(
            select(func.count())
            .select_from(AnalysisRun)
            .where(
                AnalysisRun.user_id == user_id,
                AnalysisRun.status == "completed",
            )
        )
        or 0
    )
    failed = (
        session.scalar(
            select(func.count())
            .select_from(AnalysisRun)
            .where(
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
    rows = session.execute(
        select(
            func.min(SkillGap.display_skill),
            func.count(SkillGap.id).label("gap_count"),
        )
        .where(SkillGap.user_id == user_id)
        .group_by(SkillGap.normalized_skill)
        .order_by(func.count(SkillGap.id).desc(), func.min(SkillGap.display_skill).asc())
        .limit(limit)
    )
    return [{"skill": skill, "count": count} for skill, count in rows]
