from source.services.report_generator import generate_pdf_report, generate_text_report


def minimal_result():
    return {
        "job_details": {"job_title": "Data Engineer", "company_name": "Northstar Analytics"},
        "scores": {"overall_match_score": 78, "match_label": "Good Match"},
        "match_summary": {
            "headline": "Strong data fit",
            "apply_recommendation": "Apply after tailoring",
            "short_explanation": "Good core skills with a few proof gaps.",
            "top_strengths": ["Python and SQL evidence"],
            "top_concerns": ["Cloud proof is thin"],
        },
        "eligibility_risks": [],
        "resume_fix_suggestions": [],
        "project_suggestions": [],
        "certification_suggestions": [],
    }


def test_generate_text_report_contains_core_sections():
    report = generate_text_report(minimal_result())

    assert "TruthFit Resume AI - Analysis Report" in report
    assert "Job Details" in report
    assert "Scores" in report


def test_generate_pdf_report_returns_pdf_bytes():
    pdf = generate_pdf_report(minimal_result())

    assert pdf.startswith(b"%PDF-1.4")
    assert len(pdf) > 500
