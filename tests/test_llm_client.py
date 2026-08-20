import json

import pytest

from source.ai.llm_client import extract_json
from source.ai.schemas import validate_analysis_result


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


def test_validate_analysis_result_fills_missing_sections_and_clamps_scores():
    result = validate_analysis_result(
        {
            "scores": {"overall_match_score": 140, "technical_match_score": "bad"},
            "ats_keyword_coverage": "not a list",
        }
    )

    assert result["scores"]["overall_match_score"] == 100
    assert result["scores"]["technical_match_score"] == 0
    assert result["ats_keyword_coverage"] == []
    assert "job_details" in result
    assert "skills_analysis" in result
