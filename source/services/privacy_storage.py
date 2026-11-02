import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from apps.api.app.config import retention_encryption_key


def encrypt_retained_text(plaintext: str) -> tuple[str, str]:
    key = _decode_key(retention_encryption_key())
    nonce = os.urandom(12)
    ciphertext = AESGCM(key).encrypt(nonce, plaintext.encode("utf-8"), None)
    return _encode(ciphertext), _encode(nonce)


def decrypt_retained_text(ciphertext: str, nonce: str) -> str:
    key = _decode_key(retention_encryption_key())
    plaintext = AESGCM(key).decrypt(_decode(nonce), _decode(ciphertext), None)
    return plaintext.decode("utf-8")


def _decode_key(encoded_key: str) -> bytes:
    if not encoded_key:
        raise ValueError(
            "Original-resume retention requires TRUTHFIT_RETENTION_ENCRYPTION_KEY."
        )
    try:
        key = _decode(encoded_key)
    except Exception as exc:
        raise ValueError("TRUTHFIT_RETENTION_ENCRYPTION_KEY must be valid base64.") from exc
    if len(key) != 32:
        raise ValueError("TRUTHFIT_RETENTION_ENCRYPTION_KEY must decode to 32 bytes.")
    return key


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value.encode("ascii"))
