from urllib.parse import urlparse


def is_valid_http_url(value: str) -> bool:
    parsed = urlparse((value or "").strip())

    if parsed.scheme not in {"http", "https"}:
        return False

    if not parsed.netloc:
        return False

    return not any(char.isspace() for char in value)
