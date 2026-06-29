import json
from datetime import date
from pathlib import Path

import pandas as pd


TRACKER_DIR = Path(".truthfit")
TRACKER_PATH = TRACKER_DIR / "jobs.json"

TRACKER_COLUMNS = [
    "Company",
    "Role",
    "Job Link",
    "Status",
    "Location",
    "Salary Expectation",
    "Applied Date",
    "Follow-up Date",
    "Match Score",
    "Priority",
    "Notes",
]

STATUS_OPTIONS = [
    "Wishlist",
    "Applied",
    "Interview",
    "Offer",
    "Rejected",
    "Paused",
]

PRIORITY_OPTIONS = ["Important", "Would help", "Nice to have"]


def empty_tracker_df() -> pd.DataFrame:
    return pd.DataFrame(columns=TRACKER_COLUMNS)


def normalize_tracker_df(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()

    for column in TRACKER_COLUMNS:
        if column not in normalized.columns:
            normalized[column] = ""

    normalized = normalized[TRACKER_COLUMNS].fillna("")
    normalized = normalized.replace({"None": "", "nan": "", "NaN": ""})

    if normalized.empty:
        return normalized

    non_empty = normalized.apply(
        lambda row: any(str(value).strip() for value in row),
        axis=1,
    )
    return normalized[non_empty].reset_index(drop=True)


def load_job_tracker() -> pd.DataFrame:
    if not TRACKER_PATH.exists():
        return empty_tracker_df()

    try:
        rows = json.loads(TRACKER_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return empty_tracker_df()

    df = pd.DataFrame(rows)

    return normalize_tracker_df(df)


def save_job_tracker(df: pd.DataFrame) -> None:
    TRACKER_DIR.mkdir(exist_ok=True)
    normalized = normalize_tracker_df(df)
    TRACKER_PATH.write_text(
        json.dumps(normalized.to_dict(orient="records"), indent=2),
        encoding="utf-8",
    )


def _clean_text(value) -> str:
    if value is None:
        return ""

    text = str(value).strip()
    return "" if text.lower() in ["none", "nan", "null"] else text


def _salary_from_job(job: dict) -> str:
    salary = _clean_text(job.get("salary_range", ""))
    return salary or "Not specified in JD"


def _priority_from_analysis(result: dict) -> str:
    scores = result.get("scores", {})
    risks = result.get("eligibility_risks", []) + result.get("jd_red_flags", [])
    score = int(scores.get("overall_match_score", 0) or 0)

    has_high_risk = any(
        _clean_text(item.get("severity", "")).lower() == "high"
        for item in risks
        if isinstance(item, dict)
    )

    if has_high_risk or score < 50:
        return "Nice to have"

    if score >= 75:
        return "Important"

    return "Would help"


def _notes_from_analysis(result: dict) -> str:
    scores = result.get("scores", {})
    summary = result.get("match_summary", {})
    risks = result.get("eligibility_risks", []) + result.get("jd_red_flags", [])

    score = _clean_text(scores.get("overall_match_score", ""))
    label = _clean_text(scores.get("match_label", ""))
    recommendation = _clean_text(summary.get("apply_recommendation", ""))
    headline = _clean_text(summary.get("headline", ""))

    high_risks = [
        _clean_text(item.get("risk_type") or item.get("flag"))
        for item in risks
        if isinstance(item, dict) and _clean_text(item.get("severity", "")).lower() == "high"
    ]

    parts = []

    if score:
        parts.append(f"Match score: {score}/100")
    if label:
        parts.append(label)
    if recommendation:
        parts.append(recommendation)
    if headline:
        parts.append(headline)
    if high_risks:
        parts.append(f"Important risk item: {high_risks[0]}")

    return " | ".join(parts) or "Added from TruthFit analysis."


def new_job_from_analysis(result: dict) -> dict:
    job = result.get("job_details", {})
    scores = result.get("scores", {})
    score = int(scores.get("overall_match_score", 0) or 0)

    return {
        "Company": _clean_text(job.get("company_name", "")) or "Not specified",
        "Role": _clean_text(job.get("job_title", "")) or "Not specified",
        "Job Link": _clean_text(job.get("job_link", "")),
        "Status": "Wishlist",
        "Location": _clean_text(job.get("location_or_work_policy", "")) or "Not specified",
        "Salary Expectation": _salary_from_job(job),
        "Applied Date": "",
        "Follow-up Date": str(date.today()),
        "Match Score": score,
        "Priority": _priority_from_analysis(result),
        "Notes": _notes_from_analysis(result),
    }
