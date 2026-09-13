from typing import Any

from pydantic import BaseModel, Field, field_validator

from source.ai.providers import PROVIDER_MODELS


class HealthResponse(BaseModel):
    status: str
    service: str
    database: str = "unknown"


class ErrorResponse(BaseModel):
    request_id: str
    detail: str


class ResumeParseResponse(BaseModel):
    request_id: str
    filename: str
    text: str
    redacted_text: str
    char_count: int
    redacted_char_count: int


class JobParseResponse(BaseModel):
    request_id: str
    filename: str | None = None
    text: str
    char_count: int
    job_link: str = ""


class ProviderInfo(BaseModel):
    name: str
    models: list[str]
    default_model: str


class ProvidersResponse(BaseModel):
    providers: list[ProviderInfo]


class AnalysisRunRequest(BaseModel):
    resume_text: str = Field(min_length=1)
    job_description: str = Field(min_length=1)
    include_cover_letter: bool = False
    user_projects: str = ""
    provider: str = "Gemini"
    model: str = ""
    api_key: str = ""
    job_link: str = ""
    user_email: str = ""
    resume_file_name: str = "api-resume.txt"
    job_title: str = ""
    company: str = ""

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, value: str) -> str:
        provider = (value or "Gemini").strip()
        if provider not in PROVIDER_MODELS:
            raise ValueError(f"Unsupported provider: {provider}")
        return provider


class AnalysisRunResponse(BaseModel):
    request_id: str
    run_id: str
    analysis: dict[str, Any]


class StoredAnalysisResponse(BaseModel):
    run_id: str
    status: str
    provider: str
    model: str
    overall_score: int
    analysis: dict[str, Any]


class TailorRequest(BaseModel):
    analysis: dict[str, Any] | None = None
    resume_text: str = ""
    job_description: str = ""
    include_cover_letter: bool = False
    user_projects: str = ""
    provider: str = "Gemini"
    model: str = ""
    api_key: str = ""


class TailorResponse(BaseModel):
    request_id: str
    tailored_resume_content: dict[str, Any]
    before_after_bullets: list[dict[str, Any]]
    resume_fix_suggestions: list[dict[str, Any]]
    cover_letter: str = ""
