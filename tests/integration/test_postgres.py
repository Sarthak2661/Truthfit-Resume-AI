from uuid import uuid4

import pytest
from sqlalchemy import text

from apps.api.app.db import repositories
from apps.api.app.db.database import get_engine, session_scope


pytestmark = pytest.mark.integration


def test_postgres_migrations_and_repository_round_trip():
    engine = get_engine()
    assert engine.dialect.name == "postgresql"

    with engine.connect() as connection:
        revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
    assert revision == "0005_quality_controls"

    subject = f"integration:{uuid4().hex}"
    with session_scope() as session:
        user = repositories.get_or_create_user(session, subject, "integration@truthfit.local")
        resume = repositories.create_resume(session, user.id, "resume.txt", "Python and SQL")
        job = repositories.create_job(session, user.id, "Data Engineer", "Northstar", "Python, SQL, Airflow")
        run = repositories.create_analysis_run(
            session,
            user.id,
            resume.id,
            job.id,
            "Gemini",
            "gemini-3.8-flash",
            idempotency_key="postgres-integration-key",
            request_fingerprint="a" * 64,
        )
        repositories.complete_analysis_run(
            session,
            run,
            {
                "scores": {"overall_match_score": 78},
                "skills_analysis": {"missing_skills": [{"skill": "Airflow"}]},
            },
        )
        run_id = run.id
        user_id = user.id

    with session_scope() as session:
        stored = repositories.get_analysis_run(session, run_id, user_id)
        assert stored is not None
        assert stored.overall_score == 78
        assert repositories.common_skill_gaps(session, user_id) == [
            {"skill": "Airflow", "count": 1}
        ]
        user = repositories.get_or_create_user(session, subject, "integration@truthfit.local")
        repositories.delete_user_data(session, user)
