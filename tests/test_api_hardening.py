import asyncio

from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.api.app.middleware import RequestBodyLimitMiddleware, RequestTimeoutMiddleware
from apps.api.app.services import analysis_service
from tests.test_api import client, sample_analysis


def test_security_headers_and_trusted_hosts(tmp_path):
    api = client(tmp_path)

    response = api.get("/health")
    rejected = api.get("/health", headers={"host": "untrusted.example"})

    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["cache-control"] == "no-store"
    assert rejected.status_code == 400


def test_streamed_upload_stops_when_file_limit_is_crossed(monkeypatch, tmp_path):
    monkeypatch.setenv("TRUTHFIT_MAX_UPLOAD_BYTES", "1024")
    api = client(tmp_path)

    response = api.post(
        "/resumes/parse",
        files={"file": ("resume.txt", b"x" * 2048, "text/plain")},
    )

    assert response.status_code == 413
    assert "too large" in response.json()["detail"].lower()


def test_request_body_limit_rejects_content_before_endpoint_runs():
    app = FastAPI()
    app.add_middleware(RequestBodyLimitMiddleware, max_bytes=10)

    @app.post("/")
    async def endpoint():
        return {"called": True}

    response = TestClient(app).post("/", content=b"12345678901")

    assert response.status_code == 413
    assert response.json()["detail"] == "Request body is too large."


def test_request_timeout_returns_gateway_timeout():
    app = FastAPI()
    app.add_middleware(RequestTimeoutMiddleware, timeout_seconds=0.01)

    @app.get("/")
    async def slow_endpoint():
        await asyncio.sleep(0.05)
        return {"ok": True}

    response = TestClient(app).get("/")

    assert response.status_code == 504
    assert response.json()["detail"] == "Request timed out."


def test_rate_limit_returns_retry_metadata(monkeypatch, tmp_path):
    monkeypatch.setenv("TRUTHFIT_RATE_LIMIT_REQUESTS", "2")
    api = client(tmp_path)

    first = api.get("/providers")
    second = api.get("/providers")
    limited = api.get("/providers")

    assert first.status_code == 200
    assert second.status_code == 200
    assert limited.status_code == 429
    assert int(limited.headers["retry-after"]) >= 1


def test_analysis_creation_is_idempotent_per_user(monkeypatch, tmp_path):
    monkeypatch.setattr(analysis_service, "generate_resume_analysis", lambda **_: sample_analysis())
    api = client(tmp_path)
    payload = {
        "resume_text": "Python ETL SQL",
        "job_description": "Data Engineer with Python and SQL",
        "provider": "Gemini",
        "model": "gemini-3.8-flash",
    }
    headers = {"idempotency-key": "analysis-request-001"}

    first = api.post("/analysis/run", json=payload, headers=headers)
    replay = api.post("/analysis/run", json=payload, headers=headers)
    account = api.get("/account/data").json()

    assert first.status_code == 202
    assert replay.status_code == 202
    assert replay.json()["run_id"] == first.json()["run_id"]
    assert replay.json()["idempotent_replay"] is True
    assert account["analyses"] == 1
    assert account["resumes"] == 1
    assert account["jobs"] == 1

    changed_payload = {**payload, "job_description": "A different role"}
    conflict = api.post("/analysis/run", json=changed_payload, headers=headers)
    assert conflict.status_code == 400
    assert "different analysis request" in conflict.json()["detail"]


def test_analysis_list_has_bounded_pagination(monkeypatch, tmp_path):
    monkeypatch.setattr(analysis_service, "generate_resume_analysis", lambda **_: sample_analysis())
    api = client(tmp_path)
    payload = {
        "resume_text": "Python ETL SQL",
        "job_description": "Data Engineer with Python and SQL",
        "provider": "Gemini",
        "model": "gemini-3.8-flash",
    }
    for index in range(3):
        api.post(
            "/analysis/run",
            json=payload,
            headers={"idempotency-key": f"pagination-{index}"},
        )

    page = api.get("/analysis?limit=1&offset=1")
    oversized = api.get("/analysis?limit=101")

    assert page.status_code == 200
    assert len(page.json()["analyses"]) == 1
    assert page.json()["total"] == 3
    assert page.json()["limit"] == 1
    assert page.json()["offset"] == 1
    assert oversized.status_code == 422


def test_common_skill_gaps_are_aggregated_from_normalized_rows(monkeypatch, tmp_path):
    result = sample_analysis()
    result["skills_analysis"]["missing_skills"] = [
        {"skill": "Kubernetes", "priority": "Important"}
    ]
    monkeypatch.setattr(analysis_service, "generate_resume_analysis", lambda **_: result)
    api = client(tmp_path)
    payload = {
        "resume_text": "Python ETL SQL",
        "job_description": "Data Engineer with Kubernetes",
        "provider": "Gemini",
        "model": "gemini-3.8-flash",
    }
    for index in range(2):
        api.post(
            "/analysis/run",
            json=payload,
            headers={"idempotency-key": f"skill-gap-{index}"},
        )

    summary = api.get("/dashboard/summary")

    assert summary.status_code == 200
    assert summary.json()["common_skill_gaps"] == [{"skill": "Kubernetes", "count": 2}]
