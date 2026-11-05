from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


Attention = Literal["High", "Medium", "Low"]
Priority = Literal["Important", "Would help", "Nice to have"]
RequirementStatus = Literal["Supported", "Partial", "Missing"]
EvidenceStatus = Literal["Supported", "Partial", "Missing", "Unsafe"]
MatchStrength = Literal["Strong", "Partial", "Weak"]
ANALYSIS_SCHEMA_VERSION = "v1"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class JobDetails(StrictModel):
    job_title: str = ""
    company_name: str = ""
    salary_range: str = ""
    location_or_work_policy: str = ""
    employment_type: str = ""
    job_link: str = ""
    sponsorship_policy: str = ""
    experience_required: str = ""
    degree_required: str = ""
    travel_requirement: str = ""
    security_clearance: str = ""
    contract_or_full_time: str = ""
    target_region: str = ""


class ScoreModel(StrictModel):
    overall_match_score: int = Field(default=0, ge=0, le=100)
    technical_match_score: int = Field(default=0, ge=0, le=100)
    ats_keyword_coverage_score: int = Field(default=0, ge=0, le=100)
    resume_evidence_score: int = Field(default=0, ge=0, le=100)
    eligibility_score: int = Field(default=0, ge=0, le=100)
    experience_match_score: int = Field(default=0, ge=0, le=100)
    match_label: Literal["Strong Match", "Good Match", "Partial Match", "Weak Match"] = "Weak Match"


class MatchSummary(StrictModel):
    headline: str = "Analysis unavailable"
    short_explanation: str = ""
    apply_recommendation: Literal[
        "Apply confidently",
        "Apply after tailoring",
        "Improve resume first",
        "High risk",
        "Skip",
    ] = "Improve resume first"
    top_strengths: list[str] = Field(default_factory=list)
    top_concerns: list[str] = Field(default_factory=list)


class JdRedFlag(StrictModel):
    flag: str = ""
    severity: Attention = "Medium"
    jd_evidence: str = ""
    why_it_matters: str = ""
    candidate_impact: str = ""


class RequirementCategory(StrictModel):
    category: str = "Other"
    requirements: list[str] = Field(default_factory=list)
    candidate_status: MatchStrength = "Partial"


class RequirementFinding(StrictModel):
    requirement: str = ""
    status: RequirementStatus = "Missing"
    priority: Priority = "Important"
    resume_evidence: str = "Not found in resume."
    recommendation: str = ""


class JobTitleRequirement(StrictModel):
    requirement: str = ""
    status: RequirementStatus = "Missing"
    resume_evidence: str = "Not found in resume."
    recommendation: str = ""


class JdRequirements(StrictModel):
    requirement_categories: list[RequirementCategory] = Field(default_factory=list)
    must_have: list[RequirementFinding] = Field(default_factory=list)
    nice_to_have: list[RequirementFinding] = Field(default_factory=list)
    job_title_requirements: list[JobTitleRequirement] = Field(default_factory=list)


class MatchedSkill(StrictModel):
    skill: str = ""
    category: str = ""
    evidence_status: Literal["Supported", "Partial"] = "Partial"
    resume_evidence: str = "Not found in resume."


class MissingSkill(StrictModel):
    skill: str = ""
    category: str = ""
    priority: Priority = "Important"
    reason: str = ""


class NiceToHaveSkill(StrictModel):
    skill: str = ""
    category: str = ""
    status: RequirementStatus = "Missing"
    resume_evidence: str = "Not found in resume."


class SkillsAnalysis(StrictModel):
    matched_skills: list[MatchedSkill] = Field(default_factory=list)
    missing_skills: list[MissingSkill] = Field(default_factory=list)
    nice_to_have_skills: list[NiceToHaveSkill] = Field(default_factory=list)


class AtsKeywordCoverage(StrictModel):
    keyword: str = ""
    importance: Priority = "Important"
    found_in_resume: bool = False
    coverage_status: Literal["Covered", "Partial", "Missing"] = "Missing"
    resume_evidence: str = "Not found in resume."


class AtsScoreBreakdown(StrictModel):
    category: str = ""
    score: int = Field(default=0, ge=0, le=100)
    status: MatchStrength = "Weak"
    evidence: str = ""
    recommendation: str = ""


class ScoreDriver(StrictModel):
    driver: str = ""
    contribution: int = Field(default=0, ge=-100, le=100)
    direction: Literal["Positive", "Negative"] = "Positive"
    evidence: str = ""


class ConfidenceFinding(StrictModel):
    finding: str = ""
    confidence: Attention = "Medium"
    resume_evidence: str = "Not found in resume."
    jd_evidence: str = "Not found in job description."
    risk: Attention = "Medium"
    recommendation: str = ""
    verify_manually: str = ""


class FixImpact(StrictModel):
    fix: str = ""
    impact: Attention = "Medium"
    effort: Attention = "Medium"
    priority: Priority = "Would help"
    why_it_matters: str = ""
    source: Literal["Resume Fix", "Skill Gap", "Risk", "Requirement"] = "Resume Fix"


class EligibilityRisk(StrictModel):
    risk_type: str = ""
    severity: Attention = "Medium"
    jd_evidence: str = "Not found in job description."
    resume_evidence: str = "Not found in resume."
    explanation: str = ""
    recommendation: str = ""


class EvidenceMatch(StrictModel):
    jd_requirement: str = ""
    resume_evidence: str = "Not found in resume."
    match_strength: MatchStrength = "Weak"
    explanation: str = ""


class GuardrailFinding(StrictModel):
    claim_or_skill: str = ""
    status: EvidenceStatus = "Missing"
    evidence: str = "Not found in resume."
    action: str = "Remove"


class BulletRewrite(StrictModel):
    original: str = ""
    rewritten: str = ""
    evidence_status: Literal["Supported", "Partial", "Unsafe"] = "Unsafe"
    why_improved: str = ""
    risk_note: str = ""

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_keys(cls, value):
        if not isinstance(value, dict):
            return value
        normalized = dict(value)
        if "before" in normalized and "original" not in normalized:
            normalized["original"] = normalized.pop("before")
        if "after" in normalized and "rewritten" not in normalized:
            normalized["rewritten"] = normalized.pop("after")
        return normalized


class TimelineFinding(StrictModel):
    issue: str = ""
    severity: Attention = "Medium"
    evidence: str = ""
    recommendation: str = ""


class ResumeFix(StrictModel):
    issue: str = ""
    why_it_matters: str = ""
    suggested_fix: str = ""
    priority: Priority = "Would help"


class LearningPlanItem(StrictModel):
    skill: str = ""
    priority: Priority = "Would help"
    why_needed: str = ""
    learning_action: str = ""
    mini_project_idea: str = ""


class ProjectSuggestion(StrictModel):
    project_title: str = ""
    target_gap: str = ""
    why_it_helps: str = ""
    suggested_scope: str = ""
    resume_bullet_example: str = ""
    priority: Priority = "Would help"


class CertificationSuggestion(StrictModel):
    certification: str = ""
    target_gap: str = ""
    why_it_helps: str = ""
    priority: Priority = "Nice to have"
    estimated_effort: str = ""


class TailoredBullet(StrictModel):
    original_or_source: str = ""
    rewritten: str = ""
    evidence_status: Literal["Supported", "Partial", "Unsafe"] = "Unsafe"
    why_improved: str = ""


class TailoredResumeContent(StrictModel):
    tailored_summary: str = ""
    rewritten_bullets: list[TailoredBullet] = Field(default_factory=list)


class LLMAnalysisResultModel(StrictModel):
    job_details: JobDetails
    scores: ScoreModel
    match_summary: MatchSummary
    jd_red_flags: list[JdRedFlag]
    jd_requirements: JdRequirements
    skills_analysis: SkillsAnalysis
    ats_keyword_coverage: list[AtsKeywordCoverage]
    ats_score_breakdown: list[AtsScoreBreakdown]
    score_drivers: list[ScoreDriver]
    confidence_findings: list[ConfidenceFinding]
    fix_impact_matrix: list[FixImpact]
    eligibility_risks: list[EligibilityRisk]
    evidence_based_matches: list[EvidenceMatch]
    hallucination_guardrail: list[GuardrailFinding]
    before_after_bullets: list[BulletRewrite]
    resume_timeline_check: list[TimelineFinding]
    resume_fix_suggestions: list[ResumeFix]
    skill_gap_learning_plan: list[LearningPlanItem]
    project_suggestions: list[ProjectSuggestion]
    certification_suggestions: list[CertificationSuggestion]
    tailored_resume_content: TailoredResumeContent
    cover_letter: str


class EvidenceGap(StrictModel):
    claim: str = ""
    status: str = ""
    evidence: str = ""
    recommendation: str = ""


class EvidenceClaim(EvidenceGap):
    bucket: str = ""
    points: int = Field(default=0, ge=0, le=100)


class ResumeEvidenceSummary(StrictModel):
    score: int = Field(default=0, ge=0, le=100)
    supported: int = Field(default=0, ge=0)
    partial: int = Field(default=0, ge=0)
    missing: int = Field(default=0, ge=0)
    unsafe: int = Field(default=0, ge=0)
    top_gaps: list[EvidenceGap] = Field(default_factory=list)
    claim_checks: list[EvidenceClaim] = Field(default_factory=list)


class AtsFormattingCheck(StrictModel):
    check: str = ""
    status: str = ""
    severity: str = ""
    detail: str = ""
    recommendation: str = ""


class TrackerState(StrictModel):
    status: str = "Not saved"
    notes: str = ""
    priority: str = "Normal"
    applied_at: str = ""
    follow_up_date: str = ""
    updated_at: str = ""
    saved: bool = False


class AnalysisMetadata(StrictModel):
    prompt_version: str = ""
    schema_version: str = ""
    provider: str = ""
    requested_model: str = ""
    actual_model: str = ""
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    estimated_cost_micros: int | None = Field(default=None, ge=0)
    prompt_chars: int | None = Field(default=None, ge=0)
    response_chars: int | None = Field(default=None, ge=0)


class AnalysisResultModel(LLMAnalysisResultModel):
    job_details: JobDetails = Field(default_factory=JobDetails)
    scores: ScoreModel = Field(default_factory=ScoreModel)
    match_summary: MatchSummary = Field(default_factory=MatchSummary)
    jd_red_flags: list[JdRedFlag] = Field(default_factory=list)
    jd_requirements: JdRequirements = Field(default_factory=JdRequirements)
    skills_analysis: SkillsAnalysis = Field(default_factory=SkillsAnalysis)
    ats_keyword_coverage: list[AtsKeywordCoverage] = Field(default_factory=list)
    ats_score_breakdown: list[AtsScoreBreakdown] = Field(default_factory=list)
    score_drivers: list[ScoreDriver] = Field(default_factory=list)
    confidence_findings: list[ConfidenceFinding] = Field(default_factory=list)
    fix_impact_matrix: list[FixImpact] = Field(default_factory=list)
    eligibility_risks: list[EligibilityRisk] = Field(default_factory=list)
    evidence_based_matches: list[EvidenceMatch] = Field(default_factory=list)
    hallucination_guardrail: list[GuardrailFinding] = Field(default_factory=list)
    before_after_bullets: list[BulletRewrite] = Field(default_factory=list)
    resume_timeline_check: list[TimelineFinding] = Field(default_factory=list)
    resume_fix_suggestions: list[ResumeFix] = Field(default_factory=list)
    skill_gap_learning_plan: list[LearningPlanItem] = Field(default_factory=list)
    project_suggestions: list[ProjectSuggestion] = Field(default_factory=list)
    certification_suggestions: list[CertificationSuggestion] = Field(default_factory=list)
    tailored_resume_content: TailoredResumeContent = Field(default_factory=TailoredResumeContent)
    cover_letter: str = ""
    resume_heatmap_text: str = ""
    resume_evidence_summary: ResumeEvidenceSummary | None = None
    ats_formatting_checks: list[AtsFormattingCheck] = Field(default_factory=list)
    tracker: TrackerState | None = None
    analysis_metadata: AnalysisMetadata | None = None


def analysis_json_schema() -> dict:
    """Return the provider-facing contract from the models used for validation."""
    return LLMAnalysisResultModel.model_json_schema()


def default_analysis_result(error_message: str = "") -> dict:
    result = AnalysisResultModel().model_dump()
    result["match_summary"]["short_explanation"] = error_message
    result["match_summary"]["top_concerns"] = [error_message] if error_message else []
    return result


def validate_llm_analysis_result(value) -> dict:
    return LLMAnalysisResultModel.model_validate(value).model_dump()


def validate_analysis_result(value) -> dict:
    if not isinstance(value, dict):
        return default_analysis_result("Analysis output was not a JSON object.")
    merged = {**default_analysis_result(), **value}
    return AnalysisResultModel.model_validate(merged).model_dump()
