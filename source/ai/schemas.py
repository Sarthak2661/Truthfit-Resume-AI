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
