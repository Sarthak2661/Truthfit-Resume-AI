from datetime import datetime, timezone

from apps.api.app.auth import CurrentUser
from apps.api.app.config import daily_analysis_quota, retention_cleanup_enabled, retention_days
from apps.api.app.db import repositories
from apps.api.app.db.database import session_scope
from apps.api.app.errors import ResourceNotFoundError
from apps.api.app.schemas import AccountDataResponse, DataDeletionResponse


def inspect_account_data(current_user: CurrentUser) -> AccountDataResponse:
    with session_scope() as session:
        user = repositories.get_or_create_user(
            session,
            auth_subject=current_user.subject,
            email=current_user.email,
        )
        summary = repositories.account_data_summary(session, user.id)
        now = datetime.now(timezone.utc)
        return AccountDataResponse(
            **summary,
            retention_days=retention_days("completed"),
            daily_analyses_used=repositories.daily_analysis_usage_count(
                session, user.id, now.date()
            ),
            daily_analysis_limit=daily_analysis_quota(),
        )


def delete_owned_analysis(run_id: str, current_user: CurrentUser) -> None:
    with session_scope() as session:
        user = repositories.get_or_create_user(
            session,
            auth_subject=current_user.subject,
            email=current_user.email,
        )
        run = repositories.get_analysis_run(session, run_id, user.id)
        if run is None:
            raise ResourceNotFoundError("Analysis run not found.")
        repositories.delete_analysis_run(session, run)


def delete_account_data(current_user: CurrentUser) -> DataDeletionResponse:
    with session_scope() as session:
        user = repositories.get_or_create_user(
            session,
            auth_subject=current_user.subject,
            email=current_user.email,
        )
        deleted = repositories.delete_user_data(session, user)
        return DataDeletionResponse(deleted=deleted)


def cleanup_expired_data() -> dict[str, int]:
    if not retention_cleanup_enabled():
        return {"analyses": 0, "resumes": 0, "jobs": 0}

    totals = {"analyses": 0, "resumes": 0, "jobs": 0}
    with session_scope() as session:
        for run in repositories.expired_analysis_runs(session, datetime.now(timezone.utc)):
            deleted = repositories.delete_analysis_run(session, run)
            for key in totals:
                totals[key] += deleted[key]
    return totals
