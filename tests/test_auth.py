from datetime import datetime, timedelta, timezone

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jwt import InvalidAudienceError

from apps.api.app import auth
from apps.api.app.config import SupabaseAuthSettings


def test_get_current_user_uses_verified_subject(monkeypatch):
    monkeypatch.setattr(
        auth,
        "supabase_auth_settings",
        lambda: SupabaseAuthSettings(
            issuer="https://project.supabase.co/auth/v1",
            jwks_url="https://project.supabase.co/auth/v1/.well-known/jwks.json",
            audience="authenticated",
        ),
    )
    monkeypatch.setattr(
        auth,
        "_decode_access_token",
        lambda _token, _settings: {"sub": "user-123", "email": "Person@Example.com"},
    )

    current_user = auth.get_current_user(
        HTTPAuthorizationCredentials(scheme="Bearer", credentials="verified-token")
    )

    assert current_user.subject == "user-123"
    assert current_user.email == "person@example.com"


def test_get_current_user_rejects_missing_credentials():
    with pytest.raises(HTTPException) as exc_info:
        auth.get_current_user(None)

    assert exc_info.value.status_code == 401
    assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}


def test_decode_access_token_verifies_signature_issuer_and_audience(monkeypatch):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    settings = SupabaseAuthSettings(
        issuer="https://project.supabase.co/auth/v1",
        jwks_url="https://project.supabase.co/auth/v1/.well-known/jwks.json",
        audience="authenticated",
    )
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "sub": "user-123",
            "iss": settings.issuer,
            "aud": settings.audience,
            "iat": now,
            "exp": now + timedelta(minutes=5),
        },
        private_key,
        algorithm="RS256",
        headers={"kid": "test-key"},
    )

    class FakeJwksClient:
        def get_signing_key_from_jwt(self, _token):
            return type("SigningKey", (), {"key": public_key})()

    monkeypatch.setattr(auth, "_jwks_client", lambda _url: FakeJwksClient())

    claims = auth._decode_access_token(token, settings)
    assert claims["sub"] == "user-123"

    with pytest.raises(InvalidAudienceError):
        auth._decode_access_token(
            token,
            SupabaseAuthSettings(
                issuer=settings.issuer,
                jwks_url=settings.jwks_url,
                audience="wrong-audience",
            ),
        )
