from collections.abc import Iterable


def evaluate_result(case: dict, analysis: dict) -> list[str]:
    failures: list[str] = []
    expected = case.get("expected", {})
    scores = analysis.get("scores", {})
    for score_name, bounds in expected.get("score_ranges", {}).items():
        value = scores.get(score_name)
        minimum, maximum = bounds
        if not isinstance(value, (int, float)) or not minimum <= value <= maximum:
            failures.append(
                f"{score_name}={value!r} is outside expected range {minimum}-{maximum}"
            )

    evidence_text = " ".join(_evidence_strings(analysis)).casefold()
    for term in expected.get("required_evidence_terms", []):
        if str(term).casefold() not in evidence_text:
            failures.append(f"required evidence term not found: {term}")
    for term in expected.get("forbidden_claim_terms", []):
        if str(term).casefold() in evidence_text:
            failures.append(f"forbidden unsupported claim found: {term}")
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
