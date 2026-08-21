from source.services.url_utils import is_valid_http_url


def test_is_valid_http_url_accepts_http_and_https():
    assert is_valid_http_url("https://example.com/job")
    assert is_valid_http_url("http://example.com/job?id=123")


def test_is_valid_http_url_rejects_unsafe_or_malformed_values():
    assert not is_valid_http_url("javascript:alert(1)")
    assert not is_valid_http_url("example.com/job")
    assert not is_valid_http_url("https://example.com/bad link")
    assert not is_valid_http_url("")
