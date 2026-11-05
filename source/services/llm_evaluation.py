from collections.abc import Iterable


def evaluate_result(case: dict, analysis: dict) -> list[str]:
    failures: list[str] = []
    expected = case.get("expected", {})
    scores = analysis.get("scores", {})
    for score_name, bounds in expected.get("score_ranges", {}).items():
        value = scores.get(score_name)
        minimum, maximum = bounds
        if not isinstance(value, (int, float)) or not minimum <= value <= maximum:
            failures.append(f"{score_name}={value!r} is outside expected range {minimum}-{maximum}")

    evidence_text = " ".join(_evidence_strings(analysis)).casefold()
    for term in expected.get("required_evidence_terms", []):
        if str(term).casefold() not in evidence_text:
            failures.append(f"required evidence term not found: {term}")
    for term in expected.get("forbidden_claim_terms", []):
        if str(term).casefold() in evidence_text:
            failures.append(f"forbidden unsupported claim found: {term}")

    missing_skills = {
        str(item.get("skill") or "").casefold()
        for item in analysis.get("skills_analysis", {}).get("missing_skills", [])
        if isinstance(item, dict)
    }
    for skill in expected.get("required_missing_skills", []):
        if str(skill).casefold() not in missing_skills:
            failures.append(f"required missing skill was not flagged: {skill}")

    guardrail_text = " ".join(
        str(item.get("claim_or_skill") or item.get("evidence") or "")
        for item in analysis.get("hallucination_guardrail", [])
        if isinstance(item, dict)
    ).casefold()
    for term in expected.get("required_guardrail_terms", []):
        if str(term).casefold() not in guardrail_text:
            failures.append(f"required guardrail term not found: {term}")

    expected_recommendation = expected.get("apply_recommendation")
    actual_recommendation = analysis.get("match_summary", {}).get("apply_recommendation")
    if expected_recommendation and actual_recommendation != expected_recommendation:
        failures.append(
            f"apply_recommendation={actual_recommendation!r}; expected {expected_recommendation!r}"
        )
    return failures


def evaluate_suite(cases: list[dict], results: dict[str, dict]) -> dict:
    case_results = []
    for case in cases:
        case_id = str(case["id"])
        analysis = results.get(case_id)
        failures = ["result is missing"] if analysis is None else evaluate_result(case, analysis)
        case_results.append({"id": case_id, "passed": not failures, "failures": failures})
    return {
        "version": cases[0].get("version", "unknown") if cases else "unknown",
        "passed": all(item["passed"] for item in case_results),
        "cases": case_results,
    }


def _evidence_strings(analysis: dict) -> Iterable[str]:
    for section_name in ("evidence_based_matches", "confidence_findings"):
        for item in analysis.get(section_name, []):
            if isinstance(item, dict):
                for key in ("finding", "requirement", "resume_evidence", "evidence"):
                    if item.get(key):
                        yield str(item[key])
    skills = analysis.get("skills_analysis", {})
    for item in skills.get("matched_skills", []):
        if isinstance(item, dict):
            yield str(item.get("skill") or "")
            yield str(item.get("resume_evidence") or "")
