import pytest

from apps.api.app import config
from apps.api.app.schemas import AnalysisRunRequest
from apps.api.app.services.analysis_service import build_analysis_task_payload


def test_development_uses_background_queue_by_default(monkeypatch):
    monkeypatch.setenv("TRUTHFIT_ENV", "development")
    monkeypatch.delenv("TRUTHFIT_ANALYSIS_QUEUE", raising=False)
    assert config.analysis_queue_backend() == "background"


def test_production_uses_rq_by_default(monkeypatch):
    monkeypatch.setenv("TRUTHFIT_ENV", "production")
    monkeypatch.delenv("TRUTHFIT_ANALYSIS_QUEUE", raising=False)
    assert config.analysis_queue_backend() == "rq"


def test_rq_requires_redis_url(monkeypatch):
    monkeypatch.setenv("TRUTHFIT_ANALYSIS_QUEUE", "rq")
    monkeypatch.delenv("REDIS_URL", raising=False)
    with pytest.raises(RuntimeError, match="REDIS_URL"):
        config.redis_url()


def test_server_managed_queue_payload_excludes_api_key_and_raw_contact_details():
    payload = AnalysisRunRequest(
        resume_text="Sarthak Srivastava\nsarthak@example.com\n+91 99841 50955\nPython SQL",
        job_description="Data Engineer with Python and SQL",
        provider="Gemini",
        api_key="temporary-browser-key",
        retain_original_resume=True,
    )

    queued = build_analysis_task_payload(payload, server_managed_key=True)

    assert queued["api_key"] == ""
    assert queued["retain_original_resume"] is False
    assert "sarthak@example.com" not in queued["resume_text"]
    assert "99841" not in queued["resume_text"]
