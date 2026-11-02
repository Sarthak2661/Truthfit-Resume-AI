from fastapi.testclient import TestClient

from apps.api.app.auth import CurrentUser, get_current_user
from apps.api.app.db.database import configure_database_for_tests
from apps.api.app.main import create_app

TEST_USER_A = CurrentUser(subject="supabase-user-a", email="a@example.com")
TEST_USER_B = CurrentUser(subject="supabase-user-b", email="b@example.com")


def client(tmp_path, current_user: CurrentUser = TEST_USER_A) -> TestClient:
    db_path = tmp_path / "truthfit-test.db"
    configure_database_for_tests(f"sqlite:///{db_path.as_posix()}")
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: current_user
    return TestClient(app)


def sample_analysis() -> dict:
    return {
        "job_details": {
            "job_title": "Data Engineer",
            "company_name": "Northstar Analytics",
        },
        "scores": {
            "overall_match_score": 82,
            "technical_match_score": 90,
            "ats_keyword_coverage_score": 75,
            "eligibility_score": 85,
            "experience_match_score": 80,
            "match_label": "Strong Match",
        },
        "match_summary": {
            "headline": "Strong evidence fit",
            "short_explanation": "The resume supports the core data engineering requirements.",
            "apply_recommendation": "Apply after tailoring",
            "top_strengths": ["SQL", "Python"],
            "top_concerns": ["Add orchestration detail"],
        },
        "skills_analysis": {
            "matched_skills": [
                {
                    "skill": "Python",
                    "category": "Programming",
                    "evidence_status": "Supported",
                    "resume_evidence": "Built Python ETL pipelines.",
                }
            ],
            "missing_skills": [],
            "nice_to_have_skills": [],
        },
        "tailored_resume_content": {
            "tailored_summary": "Data engineer with Python and SQL experience.",
            "rewritten_bullets": [
                {
                    "original_or_source": "Worked on data tasks.",
                    "rewritten": "Built Python ETL pipelines with SQL validation.",
                    "evidence_status": "Supported",
                    "why_improved": "Adds supported tools and scope.",
                }
            ],
        },
        "before_after_bullets": [
            {
                "before": "Worked on data tasks.",
                "after": "Built Python ETL pipelines with SQL validation.",
            }
        ],
        "resume_fix_suggestions": [
            {"issue": "Missing orchestration detail", "suggested_fix": "Add Airflow or scheduling evidence."}
        ],
        "cover_letter": "Dear hiring team...",
    }


def test_health_and_providers_endpoints(tmp_path):
    api = client(tmp_path)

    health = api.get("/health")
    providers = api.get("/providers")

    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert health.json()["database"] == "ok"
    assert providers.status_code == 200
    assert providers.json()["providers"][0]["name"] == "Gemini"


def test_protected_routes_require_authentication(tmp_path):
    db_path = tmp_path / "truthfit-unauthenticated.db"
    configure_database_for_tests(f"sqlite:///{db_path.as_posix()}")
    api = TestClient(create_app())

    assert api.get("/analysis").status_code == 401
    assert api.get("/dashboard/summary").status_code == 401
    assert api.get("/tracker").status_code == 401
    assert api.post(
        "/resumes/parse",
        files={"file": ("resume.txt", b"Python SQL", "text/plain")},
    ).status_code == 401


def test_parse_resume_redacts_personal_details(tmp_path):
    api = client(tmp_path)
    resume = b"Sarthak Srivastava\nsarthak@example.com\nPython SQL PostgreSQL"

    response = api.post(
        "/resumes/parse",
        files={"file": ("resume.txt", resume, "text/plain")},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["filename"] == "resume.txt"
    assert "Python SQL PostgreSQL" in body["text"]
    assert "sarthak@example.com" not in body["redacted_text"]
    assert "[REDACTED" in body["redacted_text"]
    assert "overview" in body["sections"]
    assert body["ats_formatting_checks"]
    assert {item["check"] for item in body["ats_formatting_checks"]} >= {
        "File type",
        "Section headings",
        "Measurable impact",
    }
    assert response.headers["x-request-id"]


def test_parse_job_combines_file_text_and_pasted_text(tmp_path):
    api = client(tmp_path)

    response = api.post(
        "/jobs/parse",
        files={"file": ("job.txt", b"Uploaded JD text", "text/plain")},
        data={"pasted_text": "Pasted JD text", "job_link": "https://example.com/job/123"},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["text"] == "Uploaded JD text\n\nPasted JD text"
    assert body["job_link"] == "https://example.com/job/123"


def test_parse_job_returns_hard_and_preferred_requirements(tmp_path):
    api = client(tmp_path)

    response = api.post(
        "/jobs/parse",
        data={
            "pasted_text": (
                "Required experience with Python and SQL pipelines.\n"
                "Preferred experience with Airflow orchestration."
            )
        },
    )

    body = response.json()
    assert response.status_code == 200
    assert body["hard_requirements"] == ["Required experience with Python and SQL pipelines."]
    assert body["preferred_requirements"] == ["Preferred experience with Airflow orchestration."]


def test_parse_job_respects_requirement_section_boundaries(tmp_path):
    api = client(tmp_path)

    response = api.post(
        "/jobs/parse",
        data={
            "pasted_text": (
                "Required Qualifications\n"
                "- Strong Python and SQL skills.\n"
                "- Experience with PostgreSQL.\n"
                "Nice to Have\n"
                "- Workflow orchestration experience with Airflow.\n"
                "- Cloud deployment experience."
            )
        },
    )

    body = response.json()
    assert response.status_code == 200
    assert body["hard_requirements"] == [
        "Strong Python and SQL skills.",
        "Experience with PostgreSQL.",
    ]
    assert body["preferred_requirements"] == [
        "Workflow orchestration experience with Airflow.",
        "Cloud deployment experience.",
    ]


def test_parse_job_extracts_project_role_metadata(tmp_path):
    api = client(tmp_path)

    response = api.post(
        "/jobs/parse",
        data={
            "pasted_text": (
                "About the job\n"
                "Project Role : Data Engineer  Project Role Description : Design and maintain data solutions.\n"
                "Must have skills : Snowflake Data Warehouse\n"
                "Minimum 3 Year(s) Of Experience Is Required"
            )
        },
    )

    body = response.json()
    assert response.status_code == 200
    assert body["job_title"] == "Data Engineer"
    assert body["company"] == ""


def test_parse_job_extracts_title_and_company_from_header_lines(tmp_path):
    api = client(tmp_path)

    response = api.post(
        "/jobs/parse",
        data={
            "pasted_text": (
                "Data Engineer\n"
                "Northstar Analytics\n"
                "Hybrid - New York, NY\n"
                "Required experience with Python and SQL pipelines."
            )
        },
    )

    body = response.json()
    assert response.status_code == 200
    assert body["job_title"] == "Data Engineer"
    assert body["company"] == "Northstar Analytics"


def test_run_analysis_stores_completed_result(monkeypatch, tmp_path):
    from apps.api.app.services import analysis_service

    monkeypatch.setattr(analysis_service, "generate_resume_analysis", lambda **_: sample_analysis())
    api = client(tmp_path)

    response = api.post(
        "/analysis/run",
        json={
            "resume_text": "Sarthak Srivastava\nsarthak@example.com\nPython ETL SQL",
            "job_description": "Data Engineer with Python and SQL",
            "provider": "Gemini",
            "model": "gemini-3.8-flash",
            "job_link": "https://example.com/job/123",
            "resume_file_name": "resume.txt",
            "job_title": "Data Engineer",
            "company": "Northstar Analytics",
            "target_region": "India",
            "resume_formatting_checks": [
                {
                    "check": "File type",
                    "status": "Pass",
                    "severity": "Low",
                    "detail": "Uploaded as .txt.",
                    "recommendation": "Use DOCX or a clean text-based PDF.",
                }
            ],
        },
    )

    body = response.json()
    assert response.status_code == 202
    assert body["run_id"]
    assert body["status"] == "pending"
    assert body["status_url"] == f"/analysis/{body['run_id']}"

    stored = api.get(f"/analysis/{body['run_id']}")
    assert stored.status_code == 200
    assert stored.json()["status"] == "completed"
    assert stored.json()["overall_score"] == 82
    assert stored.json()["analysis"]["match_summary"]["headline"] == "Strong evidence fit"
    assert stored.json()["analysis"]["job_details"]["job_link"] == "https://example.com/job/123"
    assert stored.json()["analysis"]["job_details"]["target_region"] == "India"
    assert stored.json()["analysis"]["ats_formatting_checks"][0]["check"] == "File type"

    listed = api.get("/analysis")
    assert listed.status_code == 200
    assert listed.json()["analyses"][0]["run_id"] == body["run_id"]
    assert listed.json()["analyses"][0]["job_title"] == "Data Engineer"

    summary = api.get("/dashboard/summary")
    assert summary.status_code == 200
    assert summary.json()["total_runs"] == 1
    assert summary.json()["completed_runs"] == 1
    assert summary.json()["average_match_score"] == 82.0
    assert summary.json()["score_history"][0]["score"] == 82
    assert summary.json()["resume_versions"][0]["role"] == "Data Engineer"
    assert summary.json()["resume_versions"][0]["latest_resume_file_name"] == "resume.txt"

    saved = api.post(
        f"/tracker/{body['run_id']}",
        json={
            "status": "Applied",
            "notes": "Follow up next week.",
            "priority": "High",
            "applied_at": "2026-11-02",
            "follow_up_date": "2026-11-09",
        },
    )
    assert saved.status_code == 200
    assert saved.json()["tracker_status"] == "Applied"
    assert saved.json()["match_score"] == 82
    assert saved.json()["company"] == "Northstar Analytics"
    assert saved.json()["role"] == "Data Engineer"
    assert saved.json()["job_link"] == "https://example.com/job/123"
    assert saved.json()["notes"] == "Follow up next week."
    assert saved.json()["priority"] == "High"
    assert saved.json()["applied_at"] == "2026-11-02"
    assert saved.json()["follow_up_date"] == "2026-11-09"
    assert saved.json()["analysis_url"] == f"/analysis/{body['run_id']}"

    tracker = api.get("/tracker")
    assert tracker.status_code == 200
    assert tracker.json()["jobs"][0]["run_id"] == body["run_id"]
    assert tracker.json()["jobs"][0]["tracker_status"] == "Applied"

    tracked_summary = api.get("/dashboard/summary").json()
    assert tracked_summary["tracker_status_counts"]["Applied"] == 1
    assert tracked_summary["upcoming_actions"][0]["follow_up_date"] == "2026-11-09"


def test_region_context_is_sent_to_model(monkeypatch, tmp_path):
    from apps.api.app.services import analysis_service

    captured = {}

    def fake_generate_resume_analysis(**kwargs):
        captured.update(kwargs)
        return sample_analysis()

    monkeypatch.setattr(analysis_service, "generate_resume_analysis", fake_generate_resume_analysis)
    api = client(tmp_path)

    response = api.post(
        "/analysis/run",
        json={
            "resume_text": "Python ETL SQL",
            "job_description": "Data Engineer with Snowflake",
            "provider": "Gemini",
            "model": "gemini-3.8-flash",
            "target_region": "GCC",
        },
    )

    assert response.status_code == 202
    assert "Target region: GCC" in captured["job_description"]


def test_tracker_ignores_invalid_legacy_job_link(monkeypatch, tmp_path):
    from apps.api.app.services import analysis_service

    legacy_analysis = sample_analysis()
    legacy_analysis.setdefault("job_details", {})["job_link"] = "Not specified in job description"

    monkeypatch.setattr(
        analysis_service,
        "generate_resume_analysis",
        lambda **_kwargs: legacy_analysis,
    )
    api = client(tmp_path)

    created = api.post(
        "/analysis/run",
        json={
            "resume_text": "Python ETL SQL",
            "job_description": "Data Engineer with Snowflake",
            "provider": "Gemini",
            "model": "gemini-3.8-flash",
        },
    )
    run_id = created.json()["run_id"]
    assert api.post(f"/tracker/{run_id}", json={"status": "Saved"}).status_code == 200

    tracker = api.get("/tracker")
    assert tracker.status_code == 200
    assert tracker.json()["jobs"][0]["job_link"] == ""


def test_completed_analysis_can_be_read_without_rerunning_model(monkeypatch, tmp_path):
    from apps.api.app.services import analysis_service

    calls = {"count": 0}

    def fake_generate_resume_analysis(**_):
        calls["count"] += 1
        return sample_analysis()

    monkeypatch.setattr(analysis_service, "generate_resume_analysis", fake_generate_resume_analysis)
    api = client(tmp_path)

    created = api.post(
        "/analysis/run",
        json={
            "resume_text": "Python ETL SQL",
            "job_description": "Data Engineer with Python and SQL",
            "provider": "Gemini",
            "model": "gemini-3.8-flash",
        },
    ).json()

    stored = api.get(f"/analysis/{created['run_id']}")

    assert stored.status_code == 200
    assert calls["count"] == 1
    assert stored.json()["analysis"]["scores"]["overall_match_score"] == 82


def test_provider_failure_is_persisted_as_failed_run(monkeypatch, tmp_path):
    from apps.api.app.services import analysis_service
    from apps.api.app.db.database import session_scope
    from apps.api.app.db.models import AgentEvent
    from sqlalchemy import select
    from source.ai.errors import ProviderAuthenticationError

    def reject_key(**_kwargs):
        raise ProviderAuthenticationError(
            "invalid API key",
            provider="Gemini",
            model="gemini-3.8-flash",
        )

    monkeypatch.setattr(analysis_service, "generate_resume_analysis", reject_key)
    api = client(tmp_path)

    created = api.post(
        "/analysis/run",
        json={
            "resume_text": "Python ETL SQL",
            "job_description": "Data Engineer with Python and SQL",
            "provider": "Gemini",
            "model": "gemini-3.8-flash",
        },
    )

    assert created.status_code == 202
    stored = api.get(f"/analysis/{created.json()['run_id']}")
    assert stored.status_code == 200
    assert stored.json()["status"] == "failed"
    assert stored.json()["overall_score"] == 0
    assert stored.json()["analysis"]["error"] == {
        "type": "provider_authentication_error",
        "message": "The provider rejected the API key. Check the key and try again.",
    }
    summary = api.get("/dashboard/summary").json()
    assert summary["failed_runs"] == 1
    assert summary["completed_runs"] == 0
    with session_scope() as session:
        events = list(
            session.scalars(
                select(AgentEvent).where(AgentEvent.analysis_run_id == created.json()["run_id"])
            )
        )
    assert {event.status for event in events} == {"pending", "processing", "failed"}
    failed_event = next(event for event in events if event.status == "failed")
    assert failed_event.error_type == "provider_authentication_error"


def test_unsupported_provider_model_is_rejected(tmp_path):
    api = client(tmp_path)
    response = api.post(
        "/analysis/run",
        json={
            "resume_text": "Python ETL SQL",
            "job_description": "Data Engineer with Python and SQL",
            "provider": "Gemini",
            "model": "gemini-2.0-flash",
        },
    )
    assert response.status_code == 422


def test_tailor_returns_resume_improvement_sections(tmp_path):
    api = client(tmp_path)

    response = api.post(
        "/tailor",
        json={"analysis": sample_analysis()},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["tailored_resume_content"]["tailored_summary"].startswith("Data engineer")
    assert body["before_after_bullets"][0]["rewritten"].startswith("Built Python")
    assert body["cover_letter"] == "Dear hiring team..."


def test_missing_analysis_run_returns_404(tmp_path):
    api = client(tmp_path)

    response = api.get("/analysis/not-a-real-run")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_client_cannot_choose_record_owner(monkeypatch, tmp_path):
    from apps.api.app.services import analysis_service

    monkeypatch.setattr(analysis_service, "generate_resume_analysis", lambda **_: sample_analysis())
    api = client(tmp_path)

    response = api.post(
        "/analysis/run",
        json={
            "resume_text": "Python ETL SQL",
            "job_description": "Data Engineer with Python and SQL",
            "provider": "Gemini",
            "user_email": "victim@example.com",
        },
    )

    assert response.status_code == 422


def test_cross_user_analysis_and_tracker_access_returns_404(monkeypatch, tmp_path):
    from apps.api.app.services import analysis_service

    monkeypatch.setattr(analysis_service, "generate_resume_analysis", lambda **_: sample_analysis())
    api = client(tmp_path, TEST_USER_A)

    created = api.post(
        "/analysis/run",
        json={
            "resume_text": "Python ETL SQL",
            "job_description": "Data Engineer with Python and SQL",
            "provider": "Gemini",
            "job_title": "Data Engineer",
            "company": "Northstar Analytics",
        },
    )
    assert created.status_code == 202
    run_id = created.json()["run_id"]

    api.app.dependency_overrides[get_current_user] = lambda: TEST_USER_B

    assert api.get(f"/analysis/{run_id}").status_code == 404
    assert api.post(f"/tracker/{run_id}", json={"status": "Saved"}).status_code == 404
    assert api.get("/analysis").json()["analyses"] == []
    assert api.get("/tracker").json()["jobs"] == []
    assert api.get("/dashboard/summary").json()["total_runs"] == 0


def test_analysis_persists_redacted_resume_only_by_default(monkeypatch, tmp_path):
    from sqlalchemy import select

    from apps.api.app.db.database import session_scope
    from apps.api.app.db.models import Resume
    from apps.api.app.services import analysis_service

    monkeypatch.setattr(analysis_service, "generate_resume_analysis", lambda **_: sample_analysis())
    api = client(tmp_path)
    original = "Sarthak Srivastava\nsarthak@example.com\n+91 99841 50955\nPython SQL"

    response = api.post(
        "/analysis/run",
        json={
            "resume_text": original,
            "job_description": "Data Engineer with Python and SQL",
            "provider": "Gemini",
        },
    )

    assert response.status_code == 202
    with session_scope() as session:
        resume = session.scalar(select(Resume))
        assert resume is not None
        assert resume.parsed_text is None
        assert resume.encrypted_original is None
        assert resume.encryption_nonce is None
        assert resume.original_retained is False
        assert "sarthak@example.com" not in resume.redacted_text
        assert "99841" not in resume.redacted_text


def test_explicit_retention_encrypts_original_resume(monkeypatch, tmp_path):
    import base64
    import os

    from sqlalchemy import select

    from apps.api.app.db.database import session_scope
    from apps.api.app.db.models import Resume
    from apps.api.app.services import analysis_service
    from source.services.privacy_storage import decrypt_retained_text

    monkeypatch.setenv(
        "TRUTHFIT_RETENTION_ENCRYPTION_KEY",
        base64.urlsafe_b64encode(os.urandom(32)).decode("ascii"),
    )
    monkeypatch.setattr(analysis_service, "generate_resume_analysis", lambda **_: sample_analysis())
    api = client(tmp_path)
    original = "Private resume with candidate@example.com and Python experience"

    response = api.post(
        "/analysis/run",
        json={
            "resume_text": original,
            "job_description": "Data Engineer with Python",
            "provider": "Gemini",
            "retain_original_resume": True,
        },
    )

    assert response.status_code == 202
    with session_scope() as session:
        resume = session.scalar(select(Resume))
        assert resume is not None
        assert resume.parsed_text is None
        assert resume.original_retained is True
        assert original not in resume.encrypted_original
        assert decrypt_retained_text(resume.encrypted_original, resume.encryption_nonce) == original


def test_account_summary_and_owned_analysis_deletion(monkeypatch, tmp_path):
    from sqlalchemy import func, select

    from apps.api.app.db.database import session_scope
    from apps.api.app.db.models import AgentEvent, AnalysisRun, Evidence, Job, Resume
    from apps.api.app.services import analysis_service

    monkeypatch.setattr(analysis_service, "generate_resume_analysis", lambda **_: sample_analysis())
    api = client(tmp_path)
    created = api.post(
        "/analysis/run",
        json={
            "resume_text": "candidate@example.com\nPython SQL",
            "job_description": "Data Engineer with Python and SQL",
            "provider": "Gemini",
        },
    )
    run_id = created.json()["run_id"]

    summary = api.get("/account/data")
    assert summary.status_code == 200
    assert summary.json()["analyses"] == 1
    assert summary.json()["resumes"] == 1
    assert summary.json()["jobs"] == 1

    deleted = api.delete(f"/analysis/{run_id}")
    assert deleted.status_code == 204
    assert api.get(f"/analysis/{run_id}").status_code == 404
    with session_scope() as session:
        assert session.scalar(select(func.count()).select_from(AnalysisRun)) == 0
        assert session.scalar(select(func.count()).select_from(Resume)) == 0
        assert session.scalar(select(func.count()).select_from(Job)) == 0
        assert session.scalar(select(func.count()).select_from(Evidence)) == 0
        assert session.scalar(select(func.count()).select_from(AgentEvent)) == 0


def test_cross_user_cannot_delete_analysis(monkeypatch, tmp_path):
    from apps.api.app.services import analysis_service

    monkeypatch.setattr(analysis_service, "generate_resume_analysis", lambda **_: sample_analysis())
    api = client(tmp_path, TEST_USER_A)
    created = api.post(
        "/analysis/run",
        json={
            "resume_text": "Python SQL",
            "job_description": "Data Engineer with Python and SQL",
            "provider": "Gemini",
        },
    )
    run_id = created.json()["run_id"]

    api.app.dependency_overrides[get_current_user] = lambda: TEST_USER_B

    assert api.delete(f"/analysis/{run_id}").status_code == 404
    api.app.dependency_overrides[get_current_user] = lambda: TEST_USER_A
    assert api.get(f"/analysis/{run_id}").status_code == 200


def test_account_data_deletion_removes_application_records(monkeypatch, tmp_path):
    from sqlalchemy import func, select

    from apps.api.app.db.database import session_scope
    from apps.api.app.db.models import AnalysisRun, Job, Resume, User
    from apps.api.app.services import analysis_service

    monkeypatch.setattr(analysis_service, "generate_resume_analysis", lambda **_: sample_analysis())
    api = client(tmp_path)
    api.post(
        "/analysis/run",
        json={
            "resume_text": "Python SQL",
            "job_description": "Data Engineer with Python and SQL",
            "provider": "Gemini",
        },
    )

    deleted = api.delete("/account/data")

    assert deleted.status_code == 200
    assert deleted.json()["deleted"] == {"analyses": 1, "resumes": 1, "jobs": 1}
    with session_scope() as session:
        assert session.scalar(select(func.count()).select_from(User)) == 0
        assert session.scalar(select(func.count()).select_from(AnalysisRun)) == 0
        assert session.scalar(select(func.count()).select_from(Resume)) == 0
        assert session.scalar(select(func.count()).select_from(Job)) == 0


def test_expired_analysis_cleanup_respects_retention_flag(monkeypatch, tmp_path):
    from datetime import datetime, timedelta, timezone

    from sqlalchemy import select

    from apps.api.app.db.database import session_scope
    from apps.api.app.db.models import AnalysisRun
    from apps.api.app.services import analysis_service
    from apps.api.app.services.privacy_service import cleanup_expired_data

    monkeypatch.setenv("TRUTHFIT_CLEANUP_ENABLED", "true")
    monkeypatch.setattr(analysis_service, "generate_resume_analysis", lambda **_: sample_analysis())
    api = client(tmp_path)
    created = api.post(
        "/analysis/run",
        json={
            "resume_text": "Python SQL",
            "job_description": "Data Engineer with Python and SQL",
            "provider": "Gemini",
        },
    )
    run_id = created.json()["run_id"]
    with session_scope() as session:
        run = session.get(AnalysisRun, run_id)
        run.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)

    assert cleanup_expired_data() == {"analyses": 1, "resumes": 1, "jobs": 1}
    with session_scope() as session:
        assert session.scalar(select(AnalysisRun).where(AnalysisRun.id == run_id)) is None


def test_rq_queue_rejects_browser_api_keys_before_creating_run(monkeypatch, tmp_path):
    monkeypatch.setenv("TRUTHFIT_ANALYSIS_QUEUE", "rq")
    api = client(tmp_path)

    response = api.post(
        "/analysis/run",
        json={
            "resume_text": "Python SQL",
            "job_description": "Data Engineer with Python and SQL",
            "provider": "Gemini",
            "api_key": "must-not-enter-redis",
        },
    )

    assert response.status_code == 400
    assert api.get("/analysis").json()["analyses"] == []
