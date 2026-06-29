import json

from source.ai.providers import LLMConfig, call_llm_with_retry


def build_analysis_chat_prompt(
    question: str,
    analysis_result: dict,
    resume_text: str,
    job_description: str,
    mode: str = "Question",
) -> str:
    analysis_json = json.dumps(analysis_result, ensure_ascii=True)[:12000]

    return f"""
You are TruthFit Resume AI's career copilot.

Answer using only the analysis, resume text, job description, and project evidence supplied below.
Do not invent experience, skills, employers, dates, metrics, certifications, or projects.
If the user asks for a cover letter, cold email, recruiter message, resume summary, or bullet rewrite,
make it concise, professional, and truthful.

Mode: {mode}

Candidate request:
{question}

Current analysis JSON:
{analysis_json}

Resume text:
{resume_text[:6000]}

Job description:
{job_description[:5000]}

Return plain text only. Use short sections and bullets where helpful.
"""


def generate_analysis_chat_response(
    question: str,
    analysis_result: dict,
    resume_text: str,
    job_description: str,
    provider: str,
    model: str,
    api_key: str,
    mode: str = "Question",
) -> str:
    prompt = build_analysis_chat_prompt(
        question=question,
        analysis_result=analysis_result,
        resume_text=resume_text,
        job_description=job_description,
        mode=mode,
    )

    return call_llm_with_retry(
        prompt,
        LLMConfig(provider=provider, model=model, api_key=api_key),
    )
