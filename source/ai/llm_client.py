import json
import re

from source.ai.prompts import build_resume_analysis_prompt
from source.ai.providers import LLMConfig, call_llm_with_retry
from source.ai.schemas import default_analysis_result
from source.services.observability import log_warning, new_request_id, timed_operation


def extract_json(text: str) -> dict:
    if not text:
        raise json.JSONDecodeError("Empty response", "", 0)

    text = text.strip()
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        text = match.group(0)

    return json.loads(text)


def generate_resume_analysis(
    resume_text: str,
    job_description: str,
    include_cover_letter: bool = False,
    user_projects: str = "",
    provider: str = "Gemini",
    model: str = "gemini-2.5-flash",
    api_key: str = "",
) -> dict:
    request_id = new_request_id()
    resume_text = resume_text[:8000]
    job_description = job_description[:7000]
    user_projects = user_projects[:5000]

    prompt = build_resume_analysis_prompt(
        resume_text=resume_text,
        job_description=job_description,
        include_cover_letter=include_cover_letter,
        user_projects=user_projects,
    )

    try:
        with timed_operation(
            "analysis_generation",
            request_id=request_id,
            provider=provider,
            model=model,
            resume_chars=len(resume_text),
            jd_chars=len(job_description),
            project_chars=len(user_projects),
            cover_letter=include_cover_letter,
        ):
            output_text = call_llm_with_retry(
                prompt,
                LLMConfig(provider=provider, model=model, api_key=api_key),
            )
        return extract_json(output_text)

    except json.JSONDecodeError as exc:
        log_warning(
            "analysis_json_parse_failed",
            request_id=request_id,
            provider=provider,
            model=model,
            error_type=exc.__class__.__name__,
        )
        fallback = default_analysis_result(
            f"{provider} returned a response, but it was not valid JSON."
        )

        if "output_text" in locals():
            fallback["match_summary"]["short_explanation"] = output_text[:1200]

        return fallback

    except Exception as exc:
        log_warning(
            "analysis_generation_failed",
            request_id=request_id,
            provider=provider,
            model=model,
            error_type=exc.__class__.__name__,
        )
        return default_analysis_result(
            f"{provider} API error after retries/fallback models: {str(exc)}"
        )
