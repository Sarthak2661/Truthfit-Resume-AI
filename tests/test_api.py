from fastapi.testclient import TestClient

from apps.api.app.db.database import configure_database_for_tests
from apps.api.app.main import create_app


def client(tmp_path) -> TestClient:
    db_path = tmp_path / "truthfit-test.db"
    configure_database_for_tests(f"sqlite:///{db_path.as_posix()}")
    return TestClient(create_app())


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
                    "status": "Covered",
                    "importance": "Important",
                    "resume_evidence": "Built Python ETL pipelines.",
                    "action": "Keep visible.",
                }
            ],
            "missing_skills": [],
            "nice_to_have_skills": [],
        },
        "tailored_resume_content": {
            "tailored_summary": "Data engineer with Python and SQL experience.",
            "rewritten_bullets": ["Built Python ETL pipelines with SQL validation."],
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
            "model": "gemini-3.6-flash",
            "job_link": "https://example.com/job/123",
            "user_email": "demo@example.com",
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
    assert response.status_code == 200
    assert body["run_id"]
    assert body["analysis"]["scores"]["overall_match_score"] == 82
    assert body["analysis"]["job_details"]["job_link"] == "https://example.com/job/123"
    assert body["analysis"]["job_details"]["target_region"] == "India"
    assert body["analysis"]["ats_formatting_checks"][0]["check"] == "File type"

    stored = api.get(f"/analysis/{body['run_id']}")
    assert stored.status_code == 200
    assert stored.json()["status"] == "completed"
    assert stored.json()["overall_score"] == 82
    assert stored.json()["analysis"]["match_summary"]["headline"] == "Strong evidence fit"

    listed = api.get("/analysis")
    assert listed.status_code == 200
    assert listed.json()["analyses"][0]["run_id"] == body["run_id"]
    assert listed.json()["analyses"][0]["job_title"] == "Data Engineer"

    summary = api.get("/dashboard/summary")
    assert summary.status_code == 200
    assert summary.json()["total_runs"] == 1
    assert summary.json()["completed_runs"] == 1
    assert summary.json()["average_match_score"] == 82.0

    saved = api.post(f"/tracker/{body['run_id']}", json={"status": "Applied", "notes": "Follow up next week."})
    assert saved.status_code == 200
    assert saved.json()["tracker_status"] == "Applied"
    assert saved.json()["match_score"] == 82
    assert saved.json()["company"] == "Northstar Analytics"
    assert saved.json()["role"] == "Data Engineer"
    assert saved.json()["job_link"] == "https://example.com/job/123"
    assert saved.json()["notes"] == "Follow up next week."
    assert saved.json()["analysis_url"] == f"/analysis/{body['run_id']}"

    tracker = api.get("/tracker")
    assert tracker.status_code == 200
    assert tracker.json()["jobs"][0]["run_id"] == body["run_id"]
    assert tracker.json()["jobs"][0]["tracker_status"] == "Applied"


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
            "model": "gemini-3.6-flash",
            "target_region": "GCC",
        },
    )

    assert response.status_code == 200
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
            "model": "gemini-3.6-flash",
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
            "model": "gemini-3.6-flash",
            "user_email": "returning@example.com",
        },
    ).json()

    stored = api.get(f"/analysis/{created['run_id']}")

    assert stored.status_code == 200
    assert calls["count"] == 1
    assert stored.json()["analysis"]["scores"]["overall_match_score"] == 82


def test_tailor_returns_resume_improvement_sections(tmp_path):
    api = client(tmp_path)

    response = api.post(
        "/tailor",
        json={"analysis": sample_analysis()},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["tailored_resume_content"]["tailored_summary"].startswith("Data engineer")
    assert body["before_after_bullets"][0]["after"].startswith("Built Python")
    assert body["cover_letter"] == "Dear hiring team..."


def test_missing_analysis_run_returns_400(tmp_path):
    api = client(tmp_path)

    response = api.get("/analysis/not-a-real-run")

    assert response.status_code == 400
    assert "not found" in response.json()["detail"].lower()
