SUPPORTED_STATUSES = {"supported", "covered", "strong", "high"}
PARTIAL_STATUSES = {"partial", "needs proof", "medium"}
MISSING_STATUSES = {"missing", "weak", "not found"}
UNSAFE_STATUSES = {"unsafe"}


def add_resume_evidence_score(result: dict) -> dict:
    if not isinstance(result, dict):
        return result

    scores = result.setdefault("scores", {})

    if not scores.get("resume_evidence_score"):
        evidence = calculate_resume_evidence_score(result)
        scores["resume_evidence_score"] = evidence["score"]
        result["resume_evidence_summary"] = evidence
    else:
        result.setdefault("resume_evidence_summary", calculate_resume_evidence_score(result))

    return result


def calculate_resume_evidence_score(result: dict) -> dict:
    records = []

    for item in result.get("confidence_findings", []):
        if isinstance(item, dict):
            evidence = item.get("resume_evidence", "")
            records.append(
                {
                    "claim": clean_value(item.get("finding", "")) or "Confidence finding",
                    "status": _status_from_evidence(evidence, item.get("confidence", "")),
                    "evidence": clean_value(evidence),
                    "recommendation": clean_value(item.get("recommendation", "")),
                }
            )

    for item in result.get("ats_keyword_coverage", []):
        if isinstance(item, dict):
            records.append(
                {
                    "claim": clean_value(item.get("keyword", "")) or "ATS keyword",
                    "status": _normalize_status(item.get("coverage_status", "")),
                    "evidence": clean_value(item.get("resume_evidence", "")),
                    "recommendation": "Add exact resume evidence if this keyword matters for the role.",
                }
            )

    requirements = result.get("jd_requirements", {})
    for group_name in ["must_have", "nice_to_have", "job_title_requirements"]:
        for item in requirements.get(group_name, []):
            if isinstance(item, dict):
                records.append(
                    {
                        "claim": clean_value(item.get("requirement", "")) or "JD requirement",
                        "status": _normalize_status(item.get("status", "")),
                        "evidence": clean_value(item.get("resume_evidence", "")),
                        "recommendation": clean_value(item.get("recommendation", "")),
                    }
                )

    for item in result.get("before_after_bullets", []):
        if isinstance(item, dict):
            records.append(
                {
                    "claim": clean_value(item.get("rewritten", "")) or clean_value(item.get("original", "")) or "Resume bullet",
                    "status": _normalize_status(item.get("evidence_status", "")),
                    "evidence": clean_value(item.get("why_improved", "")),
                    "recommendation": clean_value(item.get("risk_note", "")),
                }
            )

    for item in result.get("hallucination_guardrail", []):
        if isinstance(item, dict):
            records.append(
                {
                    "claim": clean_value(item.get("claim_or_skill", "")) or "Unsupported claim check",
                    "status": _normalize_status(item.get("status", "")),
                    "evidence": clean_value(item.get("evidence", "")),
                    "recommendation": clean_value(item.get("action", "")),
                }
            )

    scored = [_score_record(record) for record in records if record["claim"] or record["evidence"]]

    if not scored:
        return {
            "score": 0,
            "supported": 0,
            "partial": 0,
            "missing": 0,
            "unsafe": 0,
            "top_gaps": [],
            "claim_checks": [],
        }

    total = sum(item["points"] for item in scored)
    score = round(total / (len(scored) * 100) * 100)
    counts = {"supported": 0, "partial": 0, "missing": 0, "unsafe": 0}

    for item in scored:
        counts[item["bucket"]] += 1

    top_gaps = [
        {
            "claim": item["claim"],
            "status": item["bucket"].title(),
            "evidence": item["evidence"] or "Not found in resume.",
            "recommendation": item["recommendation"] or "Verify manually before using this claim.",
        }
        for item in scored
        if item["bucket"] in ["missing", "unsafe", "partial"]
    ][:6]

    return {
        "score": score,
        **counts,
        "top_gaps": top_gaps,
        "claim_checks": scored[:25],
    }


def _score_record(record: dict) -> dict:
    status = _normalize_status(record.get("status", ""))
    evidence = clean_value(record.get("evidence", ""))
    missing_evidence = not evidence or evidence.lower().startswith("not found")

    if status in SUPPORTED_STATUSES and not missing_evidence:
        bucket = "supported"
        points = 100
    elif status in SUPPORTED_STATUSES:
        bucket = "partial"
        points = 60
    elif status in PARTIAL_STATUSES:
        bucket = "partial"
        points = 55 if not missing_evidence else 40
    elif status in UNSAFE_STATUSES:
        bucket = "unsafe"
        points = 0
    else:
        bucket = "missing"
        points = 15 if not missing_evidence else 0

    return {
        **record,
        "bucket": bucket,
        "points": points,
    }


def _status_from_evidence(evidence: str, confidence: str = "") -> str:
    evidence_text = clean_value(evidence).lower()

    if not evidence_text or evidence_text.startswith("not found"):
        return "Missing"

    return _normalize_status(confidence) or "Supported"


def _normalize_status(value: str) -> str:
    normalized = clean_value(value).strip().lower()

    if normalized in SUPPORTED_STATUSES:
        return "supported"

    if normalized in PARTIAL_STATUSES:
        return "partial"

    if normalized in MISSING_STATUSES:
        return "missing"

    if normalized in UNSAFE_STATUSES:
        return "unsafe"

    return normalized


def clean_value(value) -> str:
    if value is None:
        return ""

    if isinstance(value, list):
        return ", ".join(clean_value(item) for item in value if clean_value(item))

    if isinstance(value, dict):
        return ", ".join(
            f"{str(key).replace('_', ' ').title()}: {clean_value(item)}"
            for key, item in value.items()
            if clean_value(item)
        )

    return str(value).strip()
