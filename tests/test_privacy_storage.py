import base64
import os

import pytest

from source.services.privacy_storage import decrypt_retained_text, encrypt_retained_text


def _encryption_key() -> str:
    return base64.urlsafe_b64encode(os.urandom(32)).decode("ascii")


def test_retained_text_round_trip_uses_authenticated_encryption(monkeypatch):
    original = "Private resume text with candidate@example.com"
    monkeypatch.setenv("TRUTHFIT_RETENTION_ENCRYPTION_KEY", _encryption_key())

    ciphertext, nonce = encrypt_retained_text(original)

    assert original not in ciphertext
    assert decrypt_retained_text(ciphertext, nonce) == original


def test_retained_text_requires_a_valid_key(monkeypatch):
    monkeypatch.delenv("TRUTHFIT_RETENTION_ENCRYPTION_KEY", raising=False)

    with pytest.raises(ValueError, match="TRUTHFIT_RETENTION_ENCRYPTION_KEY"):
        encrypt_retained_text("private resume")

    monkeypatch.setenv(
        "TRUTHFIT_RETENTION_ENCRYPTION_KEY",
        base64.urlsafe_b64encode(b"short-key").decode("ascii"),
    )
    with pytest.raises(ValueError, match="32 bytes"):
        encrypt_retained_text("private resume")
