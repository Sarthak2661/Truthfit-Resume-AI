from source.services.resume_heatmap import build_resume_heatmap, redact_personal_details


def test_redact_personal_details_hides_contact_header():
    resume_text = """Sarthak Srivastava
Analytics Engineer | sarthak@example.com | +1 998-410-9555 | github.com/sarthak | linkedin.com/in/sarthak

Professional Summary
Python and SQL data engineer.
123 Main Street, New York, NY 10001
"""

    redacted = redact_personal_details(resume_text)

    assert "Sarthak Srivastava" not in redacted
    assert "sarthak@example.com" not in redacted
    assert "998-410-9555" not in redacted
    assert "github.com/sarthak" not in redacted
    assert "linkedin.com/in/sarthak" not in redacted
    assert "123 Main Street" not in redacted
    assert "[REDACTED NAME]" in redacted
    assert "[REDACTED CONTACT DETAILS]" in redacted
    assert "[REDACTED ADDRESS]" in redacted


def test_redaction_heuristic_covers_realistic_resume_layouts():
    cases = [
        (
            """JANE DOE
Data Engineer | jane.doe@example.com | +1 (415) 555-0199
San Francisco, CA | linkedin.com/in/janedoe
""",
            ["JANE DOE", "jane.doe@example.com", "415", "linkedin.com/in/janedoe"],
        ),
        (
            """Rahul Mehta
rahul.mehta@email.com
+91-9876543210
github.com/rahulmehta
42 MG Road, Bengaluru
""",
            ["Rahul Mehta", "rahul.mehta@email.com", "9876543210", "github.com/rahulmehta", "42 MG Road"],
        ),
        (
            """Maria Garcia
Email: maria.garcia@test.com | Phone: 020 7946 0958
www.mariagarcia.dev
""",
            ["Maria Garcia", "maria.garcia@test.com", "020 7946 0958", "www.mariagarcia.dev"],
        ),
        (
            """AARAV SHARMA
Analytics Engineer
aarav.sharma@test.co | +971 50 123 4567 | linkedin.com/in/aarav-sharma
""",
            ["AARAV SHARMA", "aarav.sharma@test.co", "+971 50 123 4567", "linkedin.com/in/aarav-sharma"],
        ),
    ]

    checked_tokens = 0
    redacted_tokens = 0

    for resume_text, sensitive_tokens in cases:
        redacted = redact_personal_details(resume_text)
        for token in sensitive_tokens:
            checked_tokens += 1
            if token not in redacted:
                redacted_tokens += 1

    assert redacted_tokens == checked_tokens


def test_build_resume_heatmap_marks_covered_partial_and_missing_keywords():
    resume_text = """Jane Candidate
Data Engineer

Projects
Built a Python and SQL pipeline with Kafka events and dashboard monitoring.
"""
    analysis = {
        "ats_keyword_coverage": [
            {"keyword": "Python", "coverage_status": "Covered"},
            {"keyword": "SQL", "coverage_status": "Covered"},
            {"keyword": "Kafka", "coverage_status": "Covered"},
            {"keyword": "Cloud", "coverage_status": "Partial"},
            {"keyword": "Airflow", "coverage_status": "Missing"},
        ]
    }

    heatmap = build_resume_heatmap(resume_text, analysis)

    assert heatmap["summary"]["covered_keywords"] == 3
    assert heatmap["summary"]["partial_keywords"] == 1
    assert heatmap["summary"]["missing_keywords"] == 1
    assert "Airflow" in heatmap["missing_keywords"]
    assert any(line["status"] == "covered" for line in heatmap["lines"])
    assert "[REDACTED NAME]" in heatmap["redacted_resume_text"]
