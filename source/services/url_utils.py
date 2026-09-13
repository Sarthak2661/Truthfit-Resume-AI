from urllib.parse import urlparse


def is_valid_http_url(value: str) -> bool:
    parsed = urlparse((value or "").strip())

    if parsed.scheme not in {"http", "https"}:
        return False

    if not parsed.netloc:
        return False

    return not any(char.isspace() for char in value)


def normalize_http_url(value: str) -> str:
    clean_value = (value or "").strip()

    if not clean_value:
        return ""

    if not is_valid_http_url(clean_value):
        raise ValueError("Job link must be a valid http(s) URL.")

    return clean_value
