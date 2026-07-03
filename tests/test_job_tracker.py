import pandas as pd

from source.services import job_tracker


def sample_analysis(score=82):
    return {
        "job_details": {
            "company_name": "Northstar Analytics",
            "job_title": "Data Engineer",
            "job_link": "https://example.com/job",
            "location_or_work_policy": "Hybrid",
            "salary_range": "$100k-$130k",
        },
        "scores": {
            "overall_match_score": score,
            "match_label": "Good Match",
        },
        "match_summary": {
            "apply_recommendation": "Apply after tailoring",
            "headline": "Strong data fit",
        },
        "eligibility_risks": [],
        "jd_red_flags": [],
    }


def test_normalize_tracker_df_adds_missing_columns_and_removes_empty_rows():
    df = pd.DataFrame([{"Company": "Northstar Analytics"}, {"Company": ""}])

    normalized = job_tracker.normalize_tracker_df(df)

    assert list(normalized.columns) == job_tracker.TRACKER_COLUMNS
    assert len(normalized) == 1
    assert normalized.loc[0, "Company"] == "Northstar Analytics"


def test_new_job_from_analysis_fills_score_priority_notes():
    row = job_tracker.new_job_from_analysis(sample_analysis())

    assert row["Company"] == "Northstar Analytics"
    assert row["Role"] == "Data Engineer"
    assert row["Match Score"] == 82
    assert row["Priority"] == "Important"
    assert "Match score: 82/100" in row["Notes"]


def test_upsert_job_from_analysis_dedupes_same_company_and_role():
    df, message = job_tracker.upsert_job_from_analysis(job_tracker.empty_tracker_df(), sample_analysis(72))
    updated_df, updated_message = job_tracker.upsert_job_from_analysis(df, sample_analysis(91))

    assert message.startswith("Added")
    assert updated_message.startswith("Updated")
    assert len(updated_df) == 1
    assert updated_df.loc[0, "Match Score"] == 91


def test_save_and_load_job_tracker_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(job_tracker, "TRACKER_DIR", tmp_path / ".truthfit")
    monkeypatch.setattr(job_tracker, "TRACKER_PATH", tmp_path / ".truthfit" / "jobs.json")

    df, _ = job_tracker.upsert_job_from_analysis(job_tracker.empty_tracker_df(), sample_analysis())
    job_tracker.save_job_tracker(df)

    loaded = job_tracker.load_job_tracker()

    assert len(loaded) == 1
    assert loaded.loc[0, "Company"] == "Northstar Analytics"
