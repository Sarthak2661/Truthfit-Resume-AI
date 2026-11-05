import pytest

from source.ai import providers
from source.ai.errors import ProviderAuthenticationError
from source.ai.providers import LLMConfig, ProviderResponse


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

    result = providers.call_llm_with_retry(
        "prompt", LLMConfig(provider="Gemini", model="gemini-3.8-flash", api_key="key")
    )

    assert result == "ok"
    assert calls == ["gemini-3.8-flash", "gemini-3.8-flash"]


def test_call_llm_with_retry_does_not_retry_non_retryable_error(monkeypatch):
    calls = []

    def invalid_key_gemini(prompt, config):
        calls.append(config.model)
        raise ValueError("invalid api key")

    monkeypatch.setattr(providers, "_call_gemini", invalid_key_gemini)

    with pytest.raises(ProviderAuthenticationError):
        providers.call_llm_with_retry(
            "prompt", LLMConfig(provider="Gemini", model="gemini-3.8-flash", api_key="bad")
        )

    assert calls == ["gemini-3.8-flash"]


def test_call_llm_with_retry_logs_model_fallback(monkeypatch):
    events = []

    def unavailable_then_ok(prompt, config):
        if config.model == "gemini-3.7-flash":
            raise RuntimeError("503 temporarily unavailable")
        return "ok"

    monkeypatch.setattr(providers, "_call_gemini", unavailable_then_ok)
    monkeypatch.setattr(providers.time, "sleep", lambda seconds: None)
    monkeypatch.setattr(providers.random, "uniform", lambda start, end: 0)
    monkeypatch.setattr(providers, "log_event", lambda event, **fields: events.append((event, fields)))

    result = providers.call_llm_with_retry(
        "prompt", LLMConfig(provider="Gemini", model="gemini-3.7-flash", api_key="key")
    )

    assert result == "ok"
    assert any(
        event == "llm_call_model_fallback"
        and fields["requested_model"] == "gemini-3.7-flash"
        and fields["fallback_model"] == "gemini-3.8-flash"
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

    result = providers.call_llm_with_retry(
        "prompt", LLMConfig(provider="Gemini", model="gemini-2.5-flash", api_key="key")
    )

    assert result == "ok"
    assert calls == ["gemini-2.5-flash", "gemini-3.8-flash"]


def test_provider_catalog_only_contains_supported_current_models():
    assert providers.PROVIDER_MODELS == {
        "Gemini": ["gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.5-flash-lite"],
        "Claude": ["claude-sonnet-5", "claude-sonnet-4-6", "claude-haiku-4-5-20251001"],
        "OpenAI": ["gpt-6-luna", "gpt-6.1-sol", "gpt-6-astra"],
        "Perplexity": ["sonar"],
    }


def test_provider_usage_and_configured_cost_are_returned(monkeypatch):
    monkeypatch.setenv(
        "TRUTHFIT_MODEL_PRICING_JSON",
        '{"gemini-3.8-flash":{"input_usd_per_million":1,"output_usd_per_million":2}}',
    )
    monkeypatch.setattr(
        providers,
        "_call_gemini",
        lambda prompt, config: ProviderResponse(
            text="ok",
            provider="Gemini",
            requested_model=config.model,
            actual_model=config.model,
            input_tokens=1000,
            output_tokens=500,
        ),
    )

    result = providers.call_llm_with_retry(
        "prompt",
        LLMConfig(provider="Gemini", model="gemini-3.8-flash", api_key="key"),
        include_usage=True,
    )

    assert isinstance(result, ProviderResponse)
    assert result.input_tokens == 1000
    assert result.output_tokens == 500
    assert result.estimated_cost_micros == 2000
