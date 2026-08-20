import logging

from source.services import observability


def test_format_fields_uses_allowlist():
    fields = observability._format_fields(
        {
            "provider": "Gemini",
            "model": "gemini-2.5-flash",
            "api_key": "secret",
            "resume_text": "private resume",
            "company": "private company",
        }
    )

    assert "provider=Gemini" in fields
    assert "model=gemini-2.5-flash" in fields
    assert "secret" not in fields
    assert "private resume" not in fields
    assert "private company" not in fields


def test_timed_operation_logs_safe_fields(caplog):
    caplog.set_level(logging.INFO, logger=observability.LOGGER_NAME)

    with observability.timed_operation(
        "demo_event",
        provider="Gemini",
        api_key="secret",
        prompt="private prompt",
        request_id="abc123",
    ):
        pass

    messages = "\n".join(record.getMessage() for record in caplog.records)

    assert "demo_event started" in messages
    assert "demo_event completed" in messages
    assert "provider=Gemini" in messages
    assert "request_id=abc123" in messages
    assert "secret" not in messages
    assert "private prompt" not in messages
