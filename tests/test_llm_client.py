import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from source.ai.llm_client import extract_json
from source.ai.schemas import analysis_json_schema, validate_analysis_result


def test_extract_json_from_plain_json():
    assert extract_json('{"ok": true}') == {"ok": True}


def test_extract_json_from_fenced_json():
    text = """```json
{"score": 82, "label": "Good Match"}
```"""

    assert extract_json(text) == {"score": 82, "label": "Good Match"}


def test_extract_json_from_messy_llm_output():
    text = 'Here is the result:\n{"scores": {"overall_match_score": 74}}\nThanks.'

    assert extract_json(text) == {"scores": {"overall_match_score": 74}}


def test_extract_json_rejects_empty_response():
    with pytest.raises(json.JSONDecodeError):
        extract_json("")


def test_validate_analysis_result_fills_missing_sections():
    result = validate_analysis_result({"scores": {"overall_match_score": 74}})

    assert result["scores"]["overall_match_score"] == 74
    assert "job_details" in result
    assert "skills_analysis" in result


@pytest.mark.parametrize(
    "payload",
    [
        {"scores": {"overall_match_score": 140}},
        {"skills_analysis": {"matched_skills": "not a list"}},
        {"confidence_findings": [{"finding": "Python", "unexpected": "field"}]},
    ],
)
def test_validate_analysis_result_rejects_invalid_nested_structures(payload):
    with pytest.raises(ValidationError):
        validate_analysis_result(payload)


def test_generated_schema_forbids_unknown_fields():
    schema = analysis_json_schema()

    assert schema["additionalProperties"] is False
    assert schema["$defs"]["ScoreModel"]["additionalProperties"] is False
    assert schema["$defs"]["ConfidenceFinding"]["additionalProperties"] is False
    assert set(schema["required"]) >= {"scores", "skills_analysis", "confidence_findings"}


def test_checked_in_schema_matches_pydantic_contract():
    schema_path = Path(__file__).resolve().parents[1] / "docs" / "analysis-result.schema.json"

    assert json.loads(schema_path.read_text(encoding="utf-8")) == analysis_json_schema()
