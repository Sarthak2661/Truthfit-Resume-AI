import json
from pathlib import Path

import pytest

from source.services.llm_evaluation import evaluate_result, evaluate_suite


pytestmark = pytest.mark.evaluation
ROOT_DIR = Path(__file__).resolve().parents[1]


def test_versioned_baseline_meets_score_and_evidence_expectations():
    cases = json.loads((ROOT_DIR / "evaluations" / "v1" / "cases.json").read_text("utf-8"))
    results = json.loads((ROOT_DIR / "evaluations" / "v1" / "baseline-results.json").read_text("utf-8"))

    report = evaluate_suite(cases, results)

    assert report["version"] == "v1"
    assert report["passed"] is True
    assert len(report["cases"]) >= 8


def test_evaluator_reports_score_drift_and_unsupported_claims():
    case = {
        "id": "drift",
        "expected": {
            "score_ranges": {"overall_match_score": [60, 80]},
            "required_evidence_terms": ["python"],
            "forbidden_claim_terms": ["kubernetes"],
        },
    }
    analysis = {
        "scores": {"overall_match_score": 95},
        "evidence_based_matches": [{"resume_evidence": "Built Kubernetes clusters."}],
    }

    failures = evaluate_result(case, analysis)

    assert any("outside expected range" in failure for failure in failures)
    assert any("required evidence term" in failure for failure in failures)
    assert any("forbidden unsupported claim" in failure for failure in failures)
