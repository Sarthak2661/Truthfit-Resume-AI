import json

import pytest

from source.ai.llm_client import extract_json


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
