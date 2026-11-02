import pytest

from apps.api.app.config import (
    DEVELOPMENT_CORS_ORIGINS,
    allowed_cors_origins,
    runtime_environment,
    supabase_auth_settings,
)


def test_development_uses_local_cors_origins(monkeypatch):
    monkeypatch.delenv("TRUTHFIT_ENV", raising=False)
    monkeypatch.delenv("TRUTHFIT_ALLOWED_ORIGINS", raising=False)

    assert allowed_cors_origins() == list(DEVELOPMENT_CORS_ORIGINS)


def test_production_requires_explicit_cors_origins(monkeypatch):
    monkeypatch.setenv("TRUTHFIT_ENV", "production")
    monkeypatch.delenv("TRUTHFIT_ALLOWED_ORIGINS", raising=False)

    with pytest.raises(RuntimeError, match="TRUTHFIT_ALLOWED_ORIGINS is required"):
        allowed_cors_origins()


def test_runtime_environment_rejects_unknown_value(monkeypatch):
    monkeypatch.setenv("TRUTHFIT_ENV", "prodution")

    with pytest.raises(RuntimeError, match="TRUTHFIT_ENV must be one of"):
        runtime_environment()


def test_supabase_settings_derive_issuer_and_jwks(monkeypatch):
    monkeypatch.setenv("TRUTHFIT_ENV", "test")
    monkeypatch.setenv("SUPABASE_URL", "https://project.supabase.co/")
    monkeypatch.delenv("SUPABASE_JWT_ISSUER", raising=False)
    monkeypatch.delenv("SUPABASE_JWKS_URL", raising=False)
    monkeypatch.delenv("SUPABASE_JWT_AUDIENCE", raising=False)

    settings = supabase_auth_settings()

    assert settings.issuer == "https://project.supabase.co/auth/v1"
    assert settings.jwks_url.endswith("/auth/v1/.well-known/jwks.json")
    assert settings.audience == "authenticated"


def test_supabase_url_is_required(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)

    with pytest.raises(RuntimeError, match="SUPABASE_URL is required"):
        supabase_auth_settings()


def test_production_supabase_url_requires_https(monkeypatch):
    monkeypatch.setenv("TRUTHFIT_ENV", "production")
    monkeypatch.setenv("SUPABASE_URL", "http://localhost:54321")

    with pytest.raises(RuntimeError, match="must use HTTPS"):
        supabase_auth_settings()


def test_configured_cors_origins_are_validated_and_deduplicated(monkeypatch):
    monkeypatch.setenv("TRUTHFIT_ENV", "production")
    monkeypatch.setenv(
        "TRUTHFIT_ALLOWED_ORIGINS",
        "https://app.truthfit.example/,https://app.truthfit.example,http://localhost:3000",
    )

    assert allowed_cors_origins() == [
        "https://app.truthfit.example",
        "http://localhost:3000",
    ]


@pytest.mark.parametrize(
    "origin",
    [
        "*",
        "app.truthfit.example",
        "ftp://app.truthfit.example",
        "https://app.truthfit.example/path",
        "https://user:password@app.truthfit.example",
        "https://app.truthfit.example:invalid",
    ],
)
def test_invalid_cors_origins_are_rejected(monkeypatch, origin):
    monkeypatch.setenv("TRUTHFIT_ALLOWED_ORIGINS", origin)

    with pytest.raises(RuntimeError):
        allowed_cors_origins()
