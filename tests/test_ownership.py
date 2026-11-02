from apps.api.app.db import repositories
from apps.api.app.db.database import configure_database_for_tests, session_scope


def test_analysis_queries_are_scoped_to_authenticated_owner(tmp_path):
    db_path = tmp_path / "truthfit-ownership.db"
    configure_database_for_tests(f"sqlite:///{db_path.as_posix()}")

    with session_scope() as session:
        owner = repositories.get_or_create_user(session, "owner-sub", "owner@example.com")
        other_user = repositories.get_or_create_user(session, "other-sub", "other@example.com")
        resume = repositories.create_resume(session, owner.id, "resume.txt", "Python", "Python")
        job = repositories.create_job(session, owner.id, "Data Engineer", "Northstar", "Python")
        run = repositories.create_analysis_run(
            session,
            owner.id,
            resume.id,
            job.id,
            "Gemini",
            "gemini-3.8-flash",
        )
        repositories.complete_analysis_run(
            session,
            run,
            {
                "scores": {"overall_match_score": 80},
                "skills_analysis": {"missing_skills": [{"skill": "Airflow"}]},
            },
        )
        run_id = run.id
        owner_id = owner.id
        other_user_id = other_user.id

    with session_scope() as session:
        assert repositories.get_analysis_run(session, run_id, owner_id) is not None
        assert repositories.get_analysis_run(session, run_id, other_user_id) is None
        assert [item.id for item in repositories.list_analysis_runs(session, owner_id)] == [run_id]
        assert repositories.list_analysis_runs(session, other_user_id) == []
        assert repositories.analysis_counts(session, owner_id)["total"] == 1
        assert repositories.analysis_counts(session, other_user_id)["total"] == 0
        assert repositories.common_skill_gaps(session, owner_id) == [{"skill": "Airflow", "count": 1}]
        assert repositories.common_skill_gaps(session, other_user_id) == []
