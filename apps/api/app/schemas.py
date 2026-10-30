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
    sections: dict[str, str] = Field(default_factory=dict)
    ats_formatting_checks: list[dict[str, Any]] = Field(default_factory=list)


class JobParseResponse(BaseModel):
    request_id: str
    filename: str | None = None
    text: str
    char_count: int
    job_link: str = ""
    job_title: str = ""
    company: str = ""
    hard_requirements: list[str] = Field(default_factory=list)
    preferred_requirements: list[str] = Field(default_factory=list)


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
    resume_formatting_checks: list[dict[str, Any]] = Field(default_factory=list)
    target_region: str = "US"

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, value: str) -> str:
        provider = (value or "Gemini").strip()
        if provider not in PROVIDER_MODELS:
            raise ValueError(f"Unsupported provider: {provider}")
        return provider

    @field_validator("target_region")
    @classmethod
    def validate_target_region(cls, value: str) -> str:
        region = (value or "US").strip()
        supported = {"US", "India", "GCC", "Canada/Europe"}
        if region not in supported:
            raise ValueError(f"Unsupported target region: {region}")
        return region


class AnalysisRunResponse(BaseModel):
    request_id: str
    run_id: str
    analysis: dict[str, Any]


class AnalysisListItem(BaseModel):
    run_id: str
    status: str
    provider: str
    model: str
    overall_score: int
    job_title: str = ""
    company: str = ""
    created_at: str
    completed_at: str | None = None


class AnalysisListResponse(BaseModel):
    analyses: list[AnalysisListItem]


class DashboardSummaryResponse(BaseModel):
    total_runs: int
    completed_runs: int
    failed_runs: int
    average_match_score: float
    common_skill_gaps: list[dict[str, Any]]
    provider_usage: list[dict[str, Any]]
    recent_analyses: list[AnalysisListItem]


class TrackerUpdateRequest(BaseModel):
    status: str = "Saved"
    notes: str = ""

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        status = (value or "Saved").strip()
        allowed = {"Saved", "Applied", "Interview", "Rejected"}
        if status not in allowed:
            raise ValueError(f"Unsupported tracker status: {status}")
        return status


class TrackerItem(BaseModel):
    run_id: str
    role: str
    company: str
    location: str = ""
    job_link: str = ""
    match_score: int
    tracker_status: str
    notes: str = ""
    top_fixes: list[str] = Field(default_factory=list)
    analysis_url: str
    created_at: str


class TrackerResponse(BaseModel):
    jobs: list[TrackerItem]


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
