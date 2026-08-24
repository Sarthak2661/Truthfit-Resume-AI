import pytest

from source.ai import providers
from source.ai.providers import LLMConfig


def test_call_llm_with_retry_recovers_from_retryable_error(monkeypatch):
    calls = []

    def flaky_gemini(prompt, config):
        calls.append(config.model)
        if len(calls) == 1:
            raise RuntimeError("503 temporarily unavailable")
        return "ok"

    monkeypatch.setattr(providers, "_call_gemini", flaky_gemini)
    monkeypatch.setattr(providers.time, "sleep", lambda seconds: None)
    monkeypatch.setattr(providers.random, "uniform", lambda start, end: 0)

    result = providers.call_llm_with_retry("prompt", LLMConfig(provider="Gemini", model="gemini-2.5-flash", api_key="key"))

    assert result == "ok"
    assert calls == ["gemini-2.5-flash", "gemini-2.5-flash"]


def test_call_llm_with_retry_does_not_retry_non_retryable_error(monkeypatch):
    calls = []

    def invalid_key_gemini(prompt, config):
        calls.append(config.model)
        raise ValueError("invalid api key")

    monkeypatch.setattr(providers, "_call_gemini", invalid_key_gemini)

    with pytest.raises(ValueError):
        providers.call_llm_with_retry("prompt", LLMConfig(provider="Gemini", model="gemini-2.5-flash", api_key="bad"))

    assert calls == ["gemini-2.5-flash"]


def test_call_llm_with_retry_logs_model_fallback(monkeypatch):
    events = []

    def unavailable_then_ok(prompt, config):
        if config.model == "gemini-2.5-flash":
            raise RuntimeError("503 temporarily unavailable")
        return "ok"

    monkeypatch.setattr(providers, "_call_gemini", unavailable_then_ok)
    monkeypatch.setattr(providers.time, "sleep", lambda seconds: None)
    monkeypatch.setattr(providers.random, "uniform", lambda start, end: 0)
    monkeypatch.setattr(providers, "log_event", lambda event, **fields: events.append((event, fields)))

    result = providers.call_llm_with_retry("prompt", LLMConfig(provider="Gemini", model="gemini-2.5-flash", api_key="key"))

    assert result == "ok"
    assert any(
        event == "llm_call_model_fallback"
        and fields["requested_model"] == "gemini-2.5-flash"
        and fields["fallback_model"] == "gemini-3.6-flash"
        for event, fields in events
    )


def test_call_llm_with_retry_falls_back_when_model_is_no_longer_available(monkeypatch):
    calls = []

    def old_model_unavailable(prompt, config):
        calls.append(config.model)
        if config.model == "gemini-2.5-flash":
            raise RuntimeError(
                "404 NOT_FOUND: This model models/gemini-2.5-flash is no longer available to new users."
            )
        return "ok"

    monkeypatch.setattr(providers, "_call_gemini", old_model_unavailable)
    monkeypatch.setattr(providers.time, "sleep", lambda seconds: None)

    result = providers.call_llm_with_retry("prompt", LLMConfig(provider="Gemini", model="gemini-2.5-flash", api_key="key"))

    assert result == "ok"
    assert calls == ["gemini-2.5-flash", "gemini-3.6-flash"]
