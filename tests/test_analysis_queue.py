import pytest

from apps.api.app import config


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
