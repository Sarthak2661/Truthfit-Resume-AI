from source.services.evidence_score import add_resume_evidence_score, calculate_resume_evidence_score


def test_calculate_resume_evidence_score_rewards_supported_claims():
    result = {
        "confidence_findings": [
            {
                "finding": "Python is strongly supported",
                "confidence": "High",
                "resume_evidence": "Projects: Python fraud analytics and Kafka pipeline.",
                "recommendation": "Keep Python visible.",
            },
            {
                "finding": "Airflow is present",
                "confidence": "Low",
                "resume_evidence": "Not found in resume.",
                "recommendation": "Do not claim Airflow yet.",
            },
        ],
        "ats_keyword_coverage": [
            {"keyword": "SQL", "coverage_status": "Covered", "resume_evidence": "SQL transformations."},
            {"keyword": "Cloud", "coverage_status": "Partial", "resume_evidence": "Cloud is mentioned without services."},
        ],
        "hallucination_guardrail": [
            {"claim_or_skill": "AWS deployment", "status": "Missing", "evidence": "Not found in resume."}
        ],
    }

    summary = calculate_resume_evidence_score(result)

    assert 0 < summary["score"] < 100
    assert summary["supported"] >= 2
    assert summary["partial"] >= 1
    assert summary["missing"] >= 1
    assert any("Airflow" in item["claim"] for item in summary["top_gaps"])


def test_add_resume_evidence_score_sets_score_field():
    result = {"scores": {}, "ats_keyword_coverage": []}

    updated = add_resume_evidence_score(result)

    assert "resume_evidence_score" in updated["scores"]
    assert "resume_evidence_summary" in updated
