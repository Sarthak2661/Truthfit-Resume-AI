from source.ui.components import clean_value, normalize_analysis_result


def test_clean_value_removes_html_and_decodes_entities():
    raw = '<div class="modern-info-row"><span>Skill</span><div>Python &amp; SQL</div></div>'

    assert clean_value(raw) == "Skill Python & SQL"


def test_normalize_analysis_result_cleans_nested_html_values():
    value = {
        "summary": "<p>Good &amp; supported</p>",
        "items": [{"evidence": "<strong>Python</strong>"}],
    }

    assert normalize_analysis_result(value) == {
        "summary": "Good & supported",
        "items": [{"evidence": "Python"}],
    }
