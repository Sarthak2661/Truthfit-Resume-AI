import os
import time
import random
from dataclasses import dataclass

import requests
from dotenv import load_dotenv
from google import genai

from source.services.observability import log_event, log_warning, timed_operation

load_dotenv()


PROVIDER_MODELS = {
    "Gemini": [
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.0-flash",
    ],
    "Claude": [
        "claude-3-5-sonnet-latest",
        "claude-3-5-haiku-latest",
        "claude-3-opus-latest",
    ],
    "OpenAI": [
        "gpt-5.2",
        "gpt-5.1",
        "gpt-4.1",
    ],
    "Perplexity": [
        "sonar-pro",
        "sonar",
        "sonar-reasoning-pro",
    ],
}


@dataclass(frozen=True)
class LLMConfig:
    provider: str = "Gemini"
    model: str = "gemini-2.5-flash"
    api_key: str = ""


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


def _call_gemini(prompt: str, config: LLMConfig) -> str:
    api_key = resolve_api_key(config.provider, config.api_key)

    if not api_key:
        raise ValueError("Missing Gemini API key. Add one in the sidebar or .env.")

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=config.model,
        contents=prompt,
    )
    return response.text or ""


def _call_claude(prompt: str, config: LLMConfig) -> str:
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
    return "\n".join(
        item.get("text", "")
        for item in content
        if item.get("type") == "text"
    ).strip()


def _call_openai(prompt: str, config: LLMConfig) -> str:
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
            "temperature": 0.2,
        },
        timeout=90,
    )
    response.raise_for_status()
    payload = response.json()

    if payload.get("output_text"):
        return payload["output_text"]

    output_parts = []
    for item in payload.get("output", []):
        for content in item.get("content", []):
            if content.get("type") in ["output_text", "text"]:
                output_parts.append(content.get("text", ""))

    return "\n".join(output_parts).strip()


def _call_perplexity(prompt: str, config: LLMConfig) -> str:
    api_key = resolve_api_key(config.provider, config.api_key)

    if not api_key:
        raise ValueError("Missing Perplexity API key. Add one in the sidebar or .env.")

    response = requests.post(
        "https://api.perplexity.ai/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": config.model,
            "temperature": 0.2,
            "messages": [
                {
                    "role": "system",
                    "content": "Return concise, truthful output. Follow the user's schema exactly when one is provided.",
                },
                {"role": "user", "content": prompt},
            ],
        },
        timeout=90,
    )
    response.raise_for_status()
    payload = response.json()
    choices = payload.get("choices", [])

    if not choices:
        return ""

    return choices[0].get("message", {}).get("content", "").strip()


def call_llm_with_retry(prompt: str, config: LLMConfig) -> str:
    provider = config.provider if config.provider in PROVIDER_MODELS else "Gemini"
    models = [config.model] if config.model else models_for_provider(provider)

    for fallback_model in models_for_provider(provider):
        if fallback_model not in models:
            models.append(fallback_model)

    last_error = None

    for model in models:
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
                        return _call_claude(prompt, active_config)
                    if provider == "OpenAI":
                        return _call_openai(prompt, active_config)
                    if provider == "Perplexity":
                        return _call_perplexity(prompt, active_config)
                    return _call_gemini(prompt, active_config)

            except Exception as exc:
                last_error = exc

                if not is_retryable_error(exc):
                    log_warning(
                        "llm_call_non_retryable",
                        provider=provider,
                        model=model,
                        attempt=attempt + 1,
                        error_type=exc.__class__.__name__,
                    )
                    raise exc

                wait_seconds = (2 ** (attempt + 1)) + random.uniform(0, 1.5)
                log_event(
                    "llm_call_retry_scheduled",
                    provider=provider,
                    model=model,
                    attempt=attempt + 1,
                    wait_seconds=round(wait_seconds, 2),
                    error_type=exc.__class__.__name__,
                )
                time.sleep(wait_seconds)

    raise last_error
