from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated, Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError, PyJWKClient, PyJWKClientError

from apps.api.app.config import SupabaseAuthSettings, supabase_auth_settings


@dataclass(frozen=True)
class CurrentUser:
    subject: str
    email: str = ""


bearer_scheme = HTTPBearer(auto_error=False)


@lru_cache(maxsize=4)
def _jwks_client(jwks_url: str) -> PyJWKClient:
    return PyJWKClient(jwks_url, cache_keys=True, timeout=5)


def _decode_access_token(token: str, settings: SupabaseAuthSettings) -> dict[str, Any]:
    signing_key = _jwks_client(settings.jwks_url).get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256", "ES256", "EdDSA"],
        audience=settings.audience,
        issuer=settings.issuer,
        options={"require": ["sub", "exp", "iss", "aud"]},
    )


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> CurrentUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized()

    try:
        claims = _decode_access_token(credentials.credentials, supabase_auth_settings())
    except (InvalidTokenError, PyJWKClientError, RuntimeError, ValueError):
        raise _unauthorized() from None

    subject = str(claims.get("sub") or "").strip()
    if not subject:
        raise _unauthorized()

    email = str(claims.get("email") or "").strip().lower()
    return CurrentUser(subject=subject, email=email)


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication is required.",
        headers={"WWW-Authenticate": "Bearer"},
    )
