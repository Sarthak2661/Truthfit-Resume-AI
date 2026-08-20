from pydantic import BaseModel, ConfigDict, Field, field_validator


LIST_FIELDS = [
    "jd_red_flags",
    "ats_keyword_coverage",
    "ats_score_breakdown",
    "score_drivers",
    "confidence_findings",
    "fix_impact_matrix",
    "eligibility_risks",
    "evidence_based_matches",
    "hallucination_guardrail",
    "before_after_bullets",
    "resume_timeline_check",
    "resume_fix_suggestions",
    "skill_gap_learning_plan",
    "project_suggestions",
    "certification_suggestions",
]


class ScoreModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    overall_match_score: int = 0
    technical_match_score: int = 0
    ats_keyword_coverage_score: int = 0
    resume_evidence_score: int = 0
    eligibility_score: int = 0
    experience_match_score: int = 0
    match_label: str = "Weak Match"

    @field_validator(
        "overall_match_score",
        "technical_match_score",
        "ats_keyword_coverage_score",
        "resume_evidence_score",
        "eligibility_score",
        "experience_match_score",
        mode="before",
    )
    @classmethod
    def clamp_score(cls, value):
        try:
            score = int(value or 0)
        except (TypeError, ValueError):
            return 0

        return max(0, min(100, score))


class AnalysisResultModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    job_details: dict = Field(default_factory=dict)
    scores: ScoreModel = Field(default_factory=ScoreModel)
    match_summary: dict = Field(default_factory=dict)
    jd_red_flags: list = Field(default_factory=list)
    jd_requirements: dict = Field(default_factory=dict)
    skills_analysis: dict = Field(default_factory=dict)
    ats_keyword_coverage: list = Field(default_factory=list)
    ats_score_breakdown: list = Field(default_factory=list)
    score_drivers: list = Field(default_factory=list)
    confidence_findings: list = Field(default_factory=list)
    fix_impact_matrix: list = Field(default_factory=list)
    eligibility_risks: list = Field(default_factory=list)
    evidence_based_matches: list = Field(default_factory=list)
    hallucination_guardrail: list = Field(default_factory=list)
    before_after_bullets: list = Field(default_factory=list)
    resume_timeline_check: list = Field(default_factory=list)
    resume_fix_suggestions: list = Field(default_factory=list)
    skill_gap_learning_plan: list = Field(default_factory=list)
    project_suggestions: list = Field(default_factory=list)
    certification_suggestions: list = Field(default_factory=list)
    tailored_resume_content: dict = Field(default_factory=dict)
    cover_letter: str = ""

    @field_validator(*LIST_FIELDS, mode="before")
    @classmethod
    def ensure_list(cls, value):
        return value if isinstance(value, list) else []

    @field_validator(
        "job_details",
        "match_summary",
        "jd_requirements",
        "skills_analysis",
        "tailored_resume_content",
        mode="before",
    )
    @classmethod
    def ensure_dict(cls, value):
        return value if isinstance(value, dict) else {}


def default_analysis_result(error_message: str = "") -> dict:
    return {
        "job_details": {
            "job_title": "",
            "company_name": "",
            "salary_range": "",
            "location_or_work_policy": "",
            "employment_type": "",
            "job_link": "",
            "sponsorship_policy": "",
            "experience_required": "",
            "degree_required": "",
            "travel_requirement": "",
            "security_clearance": "",
            "contract_or_full_time": ""
        },
        "scores": {
            "overall_match_score": 0,
            "technical_match_score": 0,
            "ats_keyword_coverage_score": 0,
            "resume_evidence_score": 0,
            "eligibility_score": 0,
            "experience_match_score": 0,
            "match_label": "Weak Match"
        },
        "match_summary": {
            "headline": "Analysis unavailable",
            "short_explanation": error_message,
            "apply_recommendation": "Improve resume first",
            "top_strengths": [],
            "top_concerns": [error_message] if error_message else []
        },
        "jd_red_flags": [],
        "jd_requirements": {
            "requirement_categories": [],
            "must_have": [],
            "nice_to_have": [],
            "job_title_requirements": []
        },
        "skills_analysis": {
            "matched_skills": [],
            "missing_skills": [],
            "nice_to_have_skills": []
        },
        "ats_keyword_coverage": [],
        "ats_score_breakdown": [],
        "score_drivers": [],
        "confidence_findings": [],
        "fix_impact_matrix": [],
        "eligibility_risks": [],
        "evidence_based_matches": [],
        "hallucination_guardrail": [],
        "before_after_bullets": [],
        "resume_timeline_check": [],
        "resume_fix_suggestions": [],
        "skill_gap_learning_plan": [],
        "project_suggestions": [],
        "certification_suggestions": [],
        "tailored_resume_content": {
            "tailored_summary": "",
            "rewritten_bullets": []
        },
        "cover_letter": ""
    }


def validate_analysis_result(value) -> dict:
    base = default_analysis_result()

    if not isinstance(value, dict):
        return default_analysis_result("Analysis output was not a JSON object.")

    merged = {**base, **value}
    merged["scores"] = {**base["scores"], **value.get("scores", {})} if isinstance(value.get("scores"), dict) else base["scores"]
    merged["job_details"] = (
        {**base["job_details"], **value.get("job_details", {})}
        if isinstance(value.get("job_details"), dict)
        else base["job_details"]
    )
    merged["match_summary"] = (
        {**base["match_summary"], **value.get("match_summary", {})}
        if isinstance(value.get("match_summary"), dict)
        else base["match_summary"]
    )
    merged["jd_requirements"] = (
        {**base["jd_requirements"], **value.get("jd_requirements", {})}
        if isinstance(value.get("jd_requirements"), dict)
        else base["jd_requirements"]
    )
    merged["skills_analysis"] = (
        {**base["skills_analysis"], **value.get("skills_analysis", {})}
        if isinstance(value.get("skills_analysis"), dict)
        else base["skills_analysis"]
    )
    merged["tailored_resume_content"] = (
        {**base["tailored_resume_content"], **value.get("tailored_resume_content", {})}
        if isinstance(value.get("tailored_resume_content"), dict)
        else base["tailored_resume_content"]
    )

    return AnalysisResultModel.model_validate(merged).model_dump()
