import re
from collections import Counter


SECTION_HEADINGS = [
    "summary",
    "professional summary",
    "skills",
    "core skills",
    "experience",
    "professional experience",
    "projects",
    "selected projects",
    "education",
    "certifications",
]


def redact_personal_details(text: str) -> str:
    if not text:
        return ""

    lines = text.splitlines()
    redacted_lines = []

    first_content_seen = False

    for index, line in enumerate(lines):
        stripped = line.strip()

        if not stripped:
            redacted_lines.append(line)
            continue

        if not first_content_seen and _looks_like_name(stripped):
            redacted_lines.append("[REDACTED NAME]")
            first_content_seen = True
            continue

        first_content_seen = True

        redacted = _redact_inline_personal_details(line)

        if index < 6 and _looks_like_contact_header(stripped):
            redacted = "[REDACTED CONTACT DETAILS]"
        elif _looks_like_address(stripped):
            redacted = "[REDACTED ADDRESS]"

        redacted_lines.append(redacted)

    return "\n".join(redacted_lines).strip()


def build_resume_heatmap(resume_text: str, analysis_result: dict) -> dict:
    redacted_text = redact_personal_details(resume_text)
    keywords = _keyword_records(analysis_result)
    lines = [line.rstrip() for line in redacted_text.splitlines() if line.strip()]

    heatmap_lines = []
    section_scores = Counter()
    section_hits = Counter()

    for line in lines:
        section = _section_for_line(line)
        matches = _line_matches(line, keywords)
        covered = [item for item in matches if item["status"] == "covered"]
        partial = [item for item in matches if item["status"] == "partial"]

        if covered:
            status = "covered"
            score = min(100, 45 + len(covered) * 18 + len(partial) * 8)
        elif partial:
            status = "partial"
            score = min(100, 35 + len(partial) * 15)
        else:
            status = "neutral"
            score = 0

        if status != "neutral":
            section_scores[section] += score
            section_hits[section] += 1

        heatmap_lines.append(
            {
                "text": line,
                "section": section,
                "status": status,
                "score": score,
                "matched_keywords": [item["keyword"] for item in matches[:6]],
            }
        )

    missing_keywords = [
        item["keyword"]
        for item in keywords
        if item["status"] == "missing"
    ]

    partial_keywords = [
        item["keyword"]
        for item in keywords
        if item["status"] == "partial"
    ]

    strongest_sections = [
        section
        for section, _ in section_scores.most_common(3)
    ]

    weak_sections = _weak_sections(lines, section_hits)

    return {
        "redacted_resume_text": redacted_text,
        "lines": heatmap_lines,
        "summary": {
            "highlighted_lines": sum(1 for item in heatmap_lines if item["status"] != "neutral"),
            "covered_keywords": sum(1 for item in keywords if item["status"] == "covered"),
            "partial_keywords": len(partial_keywords),
            "missing_keywords": len(missing_keywords),
            "strongest_sections": strongest_sections,
            "weak_sections": weak_sections,
        },
        "missing_keywords": missing_keywords[:12],
        "partial_keywords": partial_keywords[:12],
        "recommendations": _heatmap_recommendations(missing_keywords, partial_keywords, weak_sections),
    }


def _redact_inline_personal_details(line: str) -> str:
    redacted = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "[REDACTED EMAIL]", line)
    redacted = re.sub(r"(?i)\b(?:https?://|www\.)\S+", "[REDACTED URL]", redacted)
    redacted = re.sub(r"(?i)\b(?:github|linkedin)\.com/\S+", "[REDACTED URL]", redacted)
    redacted = re.sub(
        r"(?i)\b\d{1,6}\s+[A-Za-z0-9 .'-]+"
        r"\s(?:street|st\.?|avenue|ave\.?|road|rd\.?|lane|ln\.?|drive|dr\.?|"
        r"boulevard|blvd\.?|court|ct\.?|way|circle|cir\.?)\b[^,\n]*(?:,\s*[A-Za-z .'-]+)?(?:,\s*[A-Z]{2})?(?:\s+\d{5}(?:-\d{4})?)?",
        "[REDACTED ADDRESS]",
        redacted,
    )
    redacted = re.sub(
        r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)",
        "[REDACTED PHONE]",
        redacted,
    )
    return redacted


def _looks_like_name(line: str) -> bool:
    if any(char.isdigit() for char in line):
        return False

    if any(marker in line.lower() for marker in ["email", "phone", "linkedin", "github", "http", "@", "|"]):
        return False

    words = [word for word in re.split(r"\s+", line.strip()) if word]

    if not 2 <= len(words) <= 5:
        return False

    alpha_words = [re.sub(r"[^A-Za-z]", "", word) for word in words]
    alpha_words = [word for word in alpha_words if word]

    if len(alpha_words) < 2:
        return False

    title_like = sum(1 for word in alpha_words if word[:1].isupper())
    all_caps = sum(1 for word in alpha_words if word.isupper() and len(word) > 1)

    return title_like >= len(alpha_words) - 1 or all_caps >= len(alpha_words) - 1


def _looks_like_contact_header(line: str) -> bool:
    lower = line.lower()
    contact_markers = [
        "@",
        "linkedin",
        "github",
        "phone",
        "email",
        "open to",
        "relocation",
        "remote",
    ]
    return any(marker in lower for marker in contact_markers)


def _looks_like_address(line: str) -> bool:
    lower = line.lower()
    street_markers = [
        " street",
        " st ",
        " st.",
        " avenue",
        " ave ",
        " ave.",
        " road",
        " rd ",
        " rd.",
        " lane",
        " ln ",
        " drive",
        " dr ",
        " boulevard",
        " blvd",
        " apartment",
        " apt ",
        " suite",
    ]

    if re.search(r"\b\d{5}(?:-\d{4})?\b", line) and re.search(r"\b[A-Z]{2}\b", line):
        return True

    return bool(re.search(r"\b\d{1,6}\b", line)) and any(marker in lower for marker in street_markers)


def _keyword_records(result: dict) -> list[dict]:
    records = []

    for item in result.get("ats_keyword_coverage", []):
        if not isinstance(item, dict):
            continue

        keyword = str(item.get("keyword", "")).strip()

        if not keyword:
            continue

        records.append(
            {
                "keyword": keyword,
                "status": _coverage_status(item.get("coverage_status", "")),
                "importance": str(item.get("importance", "")).strip(),
            }
        )

    for item in result.get("skills_analysis", {}).get("matched_skills", []):
        if isinstance(item, dict) and item.get("skill"):
            records.append({"keyword": str(item["skill"]), "status": "covered", "importance": "Important"})

    for item in result.get("skills_analysis", {}).get("missing_skills", []):
        if isinstance(item, dict) and item.get("skill"):
            records.append({"keyword": str(item["skill"]), "status": "missing", "importance": str(item.get("priority", ""))})

    deduped = {}
    status_rank = {"covered": 0, "partial": 1, "missing": 2}

    for record in records:
        key = record["keyword"].lower()
        current = deduped.get(key)
        if current is None or status_rank[record["status"]] < status_rank[current["status"]]:
            deduped[key] = record

    return sorted(deduped.values(), key=lambda item: len(item["keyword"]), reverse=True)


def _coverage_status(value: str) -> str:
    normalized = str(value or "").strip().lower()

    if normalized in ["covered", "supported", "strong"]:
        return "covered"

    if normalized in ["partial", "needs proof"]:
        return "partial"

    if normalized in ["missing", "weak", "unsafe"]:
        return "missing"

    return "partial"


def _line_matches(line: str, keywords: list[dict]) -> list[dict]:
    lower = line.lower()
    matches = []

    for item in keywords:
        keyword = item["keyword"].lower()
        if len(keyword) < 2:
            continue

        if keyword in lower:
            matches.append(item)

    return matches


def _section_for_line(line: str) -> str:
    cleaned = re.sub(r"[^A-Za-z &/]", "", line).strip().lower()

    for heading in SECTION_HEADINGS:
        if cleaned == heading or cleaned.startswith(f"{heading} "):
            return heading.title()

    return "Resume Body"


def _weak_sections(lines: list[str], section_hits: Counter) -> list[str]:
    section_names = {_section_for_line(line) for line in lines}

    weak = [
        section
        for section in sorted(section_names)
        if section != "Resume Body" and section_hits[section] == 0
    ]

    return weak[:3]


def _heatmap_recommendations(missing_keywords: list[str], partial_keywords: list[str], weak_sections: list[str]) -> list[str]:
    recommendations = []

    if missing_keywords:
        recommendations.append(
            "Add missing keywords only where you have real evidence: "
            + ", ".join(missing_keywords[:5])
            + "."
        )

    if partial_keywords:
        recommendations.append(
            "Strengthen proof for partial matches by adding concrete project or work evidence: "
            + ", ".join(partial_keywords[:5])
            + "."
        )

    if weak_sections:
        recommendations.append(
            "Review low-signal sections for clearer JD alignment: "
            + ", ".join(weak_sections)
            + "."
        )

    if not recommendations:
        recommendations.append("The resume already shows strong keyword coverage. Focus on metrics and concise wording.")

    return recommendations
