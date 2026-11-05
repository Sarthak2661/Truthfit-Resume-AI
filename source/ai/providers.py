import os
import time
import random
import json
from dataclasses import dataclass

import requests
from dotenv import load_dotenv
from google import genai

from source.services.observability import log_event, log_warning, timed_operation
from source.ai.errors import (
    ProviderAuthenticationError,
    ProviderError,
    ProviderModelUnavailableError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)

load_dotenv()


PROVIDER_MODELS = {
    "Gemini": [
        "gemini-3.8-flash",
        "gemini-3.7-flash",
        "gemini-3.5-flash-lite",
    ],
    "Claude": [
        "claude-sonnet-5",
        "claude-sonnet-4-6",
        "claude-haiku-4-5-20251001",
    ],
    "OpenAI": [
        "gpt-6-luna",
        "gpt-6.1-sol",
        "gpt-6-astra",
    ],
    "Perplexity": [
        "sonar",
    ],
}


@dataclass(frozen=True)
class LLMConfig:
    provider: str = "Gemini"
    model: str = "gemini-3.8-flash"
    api_key: str = ""


@dataclass(frozen=True)
class ProviderResponse:
    text: str
    provider: str
    requested_model: str
    actual_model: str
    input_tokens: int | None = None
    output_tokens: int | None = None

    @property
    def estimated_cost_micros(self) -> int | None:
        raw_pricing = (os.getenv("TRUTHFIT_MODEL_PRICING_JSON") or "").strip()
        if not raw_pricing or self.input_tokens is None or self.output_tokens is None:
            return None
        try:
            pricing = json.loads(raw_pricing).get(self.actual_model, {})
            input_rate = float(pricing["input_usd_per_million"])
            output_rate = float(pricing["output_usd_per_million"])
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            return None
        usd = (self.input_tokens * input_rate + self.output_tokens * output_rate) / 1_000_000
        return max(0, round(usd * 1_000_000))


def provider_names() -> list[str]:
    return list(PROVIDER_MODELS.keys())


def models_for_provider(provider: str) -> list[str]:
    return PROVIDER_MODELS.get(provider, PROVIDER_MODELS["Gemini"])


def resolve_api_key(provider: str, api_key: str = "") -> str:
    if api_key:
        return api_key.strip()

    if provider == "Claude":
        return os.getenv("ANTHROPIC_API_KEY", "").strip()

    if provider == "OpenAI":
        return os.getenv("OPENAI_API_KEY", "").strip()

    if provider == "Perplexity":
        return os.getenv("PERPLEXITY_API_KEY", "").strip()

    return os.getenv("GEMINI_API_KEY", "").strip()


def is_retryable_error(error: Exception) -> bool:
    if isinstance(error, ProviderError):
        return error.retryable
    error_text = str(error).lower()
    retryable_signals = [
        "503",
        "unavailable",
        "overloaded",
        "high demand",
        "temporarily",
        "try again later",
        "429",
        "rate limit",
        "timeout",
    ]
    return any(signal in error_text for signal in retryable_signals)


def is_model_unavailable_error(error: Exception) -> bool:
    if isinstance(error, ProviderModelUnavailableError):
        return True
    error_text = str(error).lower()
    unavailable_signals = [
        "404",
        "not_found",
        "not found",
        "no longer available",
    ]
    return "model" in error_text and any(signal in error_text for signal in unavailable_signals)


def _call_gemini(prompt: str, config: LLMConfig) -> ProviderResponse:
    api_key = resolve_api_key(config.provider, config.api_key)

    if not api_key:
        raise ValueError("Missing Gemini API key. Add one in the sidebar or .env.")

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=config.model,
        contents=prompt,
    )
    usage = getattr(response, "usage_metadata", None)
    return ProviderResponse(
        text=response.text or "",
        provider=config.provider,
        requested_model=config.model,
        actual_model=config.model,
        input_tokens=getattr(usage, "prompt_token_count", None),
        output_tokens=getattr(usage, "candidates_token_count", None),
    )


def _call_claude(prompt: str, config: LLMConfig) -> ProviderResponse:
    api_key = resolve_api_key(config.provider, config.api_key)

    if not api_key:
        raise ValueError("Missing Claude API key. Add one in the sidebar or .env.")

    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": config.model,
            "max_tokens": 4096,
            "temperature": 0.2,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=90,
    )
    response.raise_for_status()
    payload = response.json()
    content = payload.get("content", [])
    text = "\n".join(item.get("text", "") for item in content if item.get("type") == "text").strip()
    usage = payload.get("usage") or {}
    return ProviderResponse(
        text=text,
        provider=config.provider,
        requested_model=config.model,
        actual_model=str(payload.get("model") or config.model),
        input_tokens=usage.get("input_tokens"),
        output_tokens=usage.get("output_tokens"),
    )


def _call_openai(prompt: str, config: LLMConfig) -> ProviderResponse:
    api_key = resolve_api_key(config.provider, config.api_key)

    if not api_key:
        raise ValueError("Missing OpenAI API key. Add one in the sidebar or .env.")

    response = requests.post(
        "https://api.openai.com/v1/responses",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": config.model,
            "input": prompt,
        },
        timeout=90,
    )
    response.raise_for_status()
    payload = response.json()

    output_parts = [str(payload["output_text"])] if payload.get("output_text") else []
    if not output_parts:
        for item in payload.get("output", []):
            for content in item.get("content", []):
                if content.get("type") in ["output_text", "text"]:
                    output_parts.append(content.get("text", ""))
    usage = payload.get("usage") or {}
    return ProviderResponse(
        text="\n".join(output_parts).strip(),
        provider=config.provider,
        requested_model=config.model,
        actual_model=str(payload.get("model") or config.model),
        input_tokens=usage.get("input_tokens"),
        output_tokens=usage.get("output_tokens"),
    )


def _call_perplexity(prompt: str, config: LLMConfig) -> ProviderResponse:
    api_key = resolve_api_key(config.provider, config.api_key)

    if not api_key:
        raise ValueError("Missing Perplexity API key. Add one in the sidebar or .env.")

    response = requests.post(
        "https://api.perplexity.ai/v1/agent",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": f"perplexity/{config.model}",
            "input": prompt,
            "max_output_tokens": 4096,
        },
        timeout=90,
    )
    response.raise_for_status()
    payload = response.json()
    output_parts = [str(payload["output_text"])] if payload.get("output_text") else []
    if not output_parts:
        for item in payload.get("output", []):
            for content in item.get("content", []):
                if content.get("type") in {"output_text", "text"}:
                    output_parts.append(str(content.get("text") or ""))
    usage = payload.get("usage") or {}
    return ProviderResponse(
        text="\n".join(output_parts).strip(),
        provider=config.provider,
        requested_model=config.model,
        actual_model=str(payload.get("model") or config.model),
        input_tokens=usage.get("input_tokens"),
        output_tokens=usage.get("output_tokens"),
    )


def _typed_provider_error(error: Exception, provider: str, model: str) -> ProviderError:
    if isinstance(error, ProviderError):
        return error

    status_code = getattr(getattr(error, "response", None), "status_code", None)
    error_text = str(error).lower()
    details = {"provider": provider, "model": model}

    if status_code in {401, 403} or any(
        signal in error_text for signal in ("invalid api key", "unauthorized", "authentication")
    ):
        return ProviderAuthenticationError(str(error), **details)
    if status_code == 429 or "rate limit" in error_text:
        return ProviderRateLimitError(str(error), **details)
    if status_code in {408, 504} or "timeout" in error_text or "timed out" in error_text:
        return ProviderTimeoutError(str(error), **details)
    if is_model_unavailable_error(error):
        return ProviderModelUnavailableError(str(error), **details)
    if (status_code is not None and status_code >= 500) or any(
        signal in error_text for signal in ("503", "unavailable", "overloaded")
    ):
        return ProviderUnavailableError(str(error), **details)
    return ProviderError(str(error), **details)


def call_llm_with_retry(
    prompt: str,
    config: LLMConfig,
    include_usage: bool = False,
) -> str | ProviderResponse:
    provider = config.provider if config.provider in PROVIDER_MODELS else "Gemini"
    models = [config.model] if config.model else models_for_provider(provider)

    for fallback_model in models_for_provider(provider):
        if fallback_model not in models:
            models.append(fallback_model)

    last_error = None

    for model in models:
        if config.model and model != config.model:
            log_event(
                "llm_call_model_fallback",
                provider=provider,
                requested_model=config.model,
                fallback_model=model,
            )

        active_config = LLMConfig(
            provider=provider,
            model=model,
            api_key=config.api_key,
        )

        for attempt in range(3):
            try:
                with timed_operation(
                    "llm_call",
                    provider=provider,
                    model=model,
                    attempt=attempt + 1,
                    prompt_chars=len(prompt),
                ):
                    if provider == "Claude":
                        response = _call_claude(prompt, active_config)
                    elif provider == "OpenAI":
                        response = _call_openai(prompt, active_config)
                    elif provider == "Perplexity":
                        response = _call_perplexity(prompt, active_config)
                    else:
                        response = _call_gemini(prompt, active_config)
                    if isinstance(response, str):
                        response = ProviderResponse(
                            text=response,
                            provider=provider,
                            requested_model=config.model,
                            actual_model=model,
                        )
                    elif response.requested_model != config.model:
                        response = ProviderResponse(
                            text=response.text,
                            provider=response.provider,
                            requested_model=config.model,
                            actual_model=response.actual_model,
                            input_tokens=response.input_tokens,
                            output_tokens=response.output_tokens,
                        )
                    return response if include_usage else response.text

            except Exception as exc:
                typed_error = _typed_provider_error(exc, provider, model)
                last_error = typed_error

                if not is_retryable_error(typed_error):
                    if is_model_unavailable_error(typed_error) and model != models[-1]:
                        log_warning(
                            "llm_call_model_unavailable",
                            provider=provider,
                            model=model,
                            attempt=attempt + 1,
                            error_type=typed_error.__class__.__name__,
                        )
                        break

                    log_warning(
                        "llm_call_non_retryable",
                        provider=provider,
                        model=model,
                        attempt=attempt + 1,
                        error_type=typed_error.__class__.__name__,
                    )
                    raise typed_error from exc

                wait_seconds = (2 ** (attempt + 1)) + random.uniform(0, 1.5)
                log_event(
                    "llm_call_retry_scheduled",
                    provider=provider,
                    model=model,
                    attempt=attempt + 1,
                    wait_seconds=round(wait_seconds, 2),
                    error_type=typed_error.__class__.__name__,
                )
                time.sleep(wait_seconds)

    if last_error is None:
        raise ProviderUnavailableError(
            "No provider model could be called.", provider=provider, model=config.model
        )
    raise last_error
