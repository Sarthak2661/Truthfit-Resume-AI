from dataclasses import dataclass
from io import BytesIO
import re

from fastapi import UploadFile

from apps.api.app.schemas import JobParseResponse, ResumeParseResponse
from source.loaders.jd_loader import extract_jd_text
from source.loaders.resume_loader import extract_text_from_file
from source.services.observability import timed_operation
from source.services.resume_heatmap import redact_personal_details
from source.services.url_utils import normalize_http_url


@dataclass
class UploadedBytes:
    content: bytes
    name: str

    @property
    def size(self) -> int:
        return len(self.content)

    def read(self, *args, **kwargs) -> bytes:
        return self._buffer.read(*args, **kwargs)

    def seek(self, *args, **kwargs):
        return self._buffer.seek(*args, **kwargs)

    def tell(self) -> int:
        return self._buffer.tell()

    def seekable(self) -> bool:
        return True

    def readable(self) -> bool:
        return True

    def __post_init__(self):
        self._buffer = BytesIO(self.content)


async def _to_uploaded_bytes(file: UploadFile | None) -> UploadedBytes | None:
    if file is None:
        return None

    content = await file.read()
    return UploadedBytes(content=content, name=file.filename or "uploaded.txt")


async def parse_resume(file: UploadFile, request_id: str) -> ResumeParseResponse:
    uploaded = await _to_uploaded_bytes(file)

    with timed_operation("api_resume_parse", request_id=request_id, file_type=_file_type(uploaded.name)):
        text = extract_text_from_file(uploaded)
        redacted_text = redact_personal_details(text)
        sections = _extract_resume_sections(redacted_text)

    return ResumeParseResponse(
        request_id=request_id,
        filename=uploaded.name,
        text=text,
        redacted_text=redacted_text,
        char_count=len(text),
        redacted_char_count=len(redacted_text),
        sections=sections,
        ats_formatting_checks=_run_ats_formatting_checks(text, uploaded.name, sections),
    )


async def parse_job_description(
    file: UploadFile | None,
    pasted_text: str,
    job_link: str,
    request_id: str,
) -> JobParseResponse:
    uploaded = await _to_uploaded_bytes(file)
    filename = uploaded.name if uploaded else None

    with timed_operation("api_job_parse", request_id=request_id, file_type=_file_type(filename or "text")):
        text = extract_jd_text(uploaded, pasted_text)
        normalized_link = normalize_http_url(job_link)

    return JobParseResponse(
        request_id=request_id,
        filename=filename,
        text=text,
        char_count=len(text),
        job_link=normalized_link,
        job_title=_extract_job_title(text),
        company=_extract_company(text),
        hard_requirements=_extract_requirements(text, preferred=False),
        preferred_requirements=_extract_requirements(text, preferred=True),
    )


def _file_type(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else "text"


def _extract_resume_sections(text: str) -> dict[str, str]:
    headings = {
        "summary": r"(?i)^(professional\s+summary|summary|profile)\b",
        "skills": r"(?i)^(core\s+skills|technical\s+skills|skills)\b",
        "experience": r"(?i)^(professional\s+experience|experience|work\s+experience)\b",
        "projects": r"(?i)^(selected\s+projects|projects|portfolio)\b",
        "education": r"(?i)^(education|certifications)\b",
    }
    sections: dict[str, list[str]] = {}
    active = "overview"

    for line in text.splitlines():
        clean_line = line.strip()
        if not clean_line:
            continue

        for name, pattern in headings.items():
            if re.search(pattern, clean_line):
                active = name
                sections.setdefault(active, [])
                break
        else:
            sections.setdefault(active, []).append(clean_line)

    return {key: "\n".join(value[:12]) for key, value in sections.items() if value}


def _run_ats_formatting_checks(text: str, filename: str, sections: dict[str, str]) -> list[dict[str, str]]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    bullets = [line for line in lines if re.match(r"^([*\-•●▪○]|\d+[.)])\s+", line)]
    file_type = _file_type(filename)

    checks = [
        _check(
            "File type",
            "Pass" if file_type in {"docx", "pdf", "txt"} else "Review",
            "Low" if file_type in {"docx", "pdf", "txt"} else "Medium",
            f"Uploaded as .{file_type}. DOCX, PDF, and TXT are supported by TruthFit.",
            "Use DOCX or a clean text-based PDF for the most reliable parsing.",
        )
    ]

    column_like_lines = [
        line
        for line in lines
        if "\t" in line or "|" in line or len(re.findall(r"\S\s{4,}\S", line)) >= 2
    ]
    checks.append(
        _check(
            "Columns or tables",
            "Review" if len(column_like_lines) >= 3 else "Pass",
            "Medium" if len(column_like_lines) >= 3 else "Low",
            (
                f"{len(column_like_lines)} line(s) look table-like or column-based."
                if column_like_lines
                else "No repeated column/table pattern was obvious in extracted text."
            ),
            "Avoid important skills or dates inside tables, columns, or text boxes when applying through ATS portals.",
        )
    )

    required_sections = {"summary", "skills", "experience", "education"}
    missing_sections = sorted(required_sections - set(sections))
    checks.append(
        _check(
            "Section headings",
            "Review" if missing_sections else "Pass",
            "Medium" if missing_sections else "Low",
            (
                f"Missing common heading(s): {', '.join(missing_sections)}."
                if missing_sections
                else "Summary, skills, experience, and education sections were detected."
            ),
            "Use simple headings like Summary, Skills, Experience, Projects, and Education.",
        )
    )

    decorative_marks = re.findall(r"[★✓✔◆■▲▶➤→↳●▪]", text)
    checks.append(
        _check(
            "Graphics or icon markers",
            "Review" if len(decorative_marks) > 18 else "Pass",
            "Medium" if len(decorative_marks) > 18 else "Low",
            (
                f"Found {len(decorative_marks)} decorative marker(s) in extracted text."
                if decorative_marks
                else "No heavy icon marker usage was detected in extracted text."
            ),
            "Keep visual icons decorative only; do not rely on them to label key resume content.",
        )
    )

    top_lines = " ".join(lines[:4])
    has_contact_at_top = bool(
        re.search(r"[\w.+-]+@[\w.-]+\.\w+", top_lines)
        or re.search(r"(\+\d{1,3}[-.\s]?)?\(?\d{3,5}\)?[-.\s]?\d{3,5}[-.\s]?\d{3,5}", top_lines)
        or re.search(r"linkedin\.com|github\.com|portfolio|location", top_lines, re.IGNORECASE)
    )
    checks.append(
        _check(
            "Header/footer risk",
            "Review" if has_contact_at_top else "Pass",
            "Low",
            (
                "Contact details appear near the top of extracted text. That is normal, but verify they are not locked inside a header/footer."
                if has_contact_at_top
                else "No obvious header/footer-only contact block was detected."
            ),
            "Place name and contact details in the main document body, not only in Word/PDF headers or footers.",
        )
    )

    long_bullets = [bullet for bullet in bullets if len(bullet) > 230]
    checks.append(
        _check(
            "Very long bullets",
            "Review" if long_bullets else "Pass",
            "Medium" if long_bullets else "Low",
            (
                f"{len(long_bullets)} bullet(s) are longer than 230 characters."
                if long_bullets
                else "No unusually long bullets were detected."
            ),
            "Keep most bullets to one or two readable lines with a clear action, tool, and result.",
        )
    )

    measurable_bullets = [bullet for bullet in bullets if re.search(r"\d|%|\$|x\b|times|hours|days|users|records", bullet, re.IGNORECASE)]
    ratio = (len(measurable_bullets) / len(bullets)) if bullets else 0
    checks.append(
        _check(
            "Measurable impact",
            "Review" if bullets and ratio < 0.3 else "Pass",
            "Medium" if bullets and ratio < 0.3 else "Low",
            (
                f"{len(measurable_bullets)} of {len(bullets)} detected bullet(s) include measurable impact."
                if bullets
                else "No bullet-style lines were detected for impact scanning."
            ),
            "Add numbers where accurate: scale, latency, accuracy, cost, volume, frequency, or business outcome.",
        )
    )

    return checks


def _check(name: str, status: str, severity: str, detail: str, recommendation: str) -> dict[str, str]:
    return {
        "check": name,
        "status": status,
        "severity": severity,
        "detail": detail,
        "recommendation": recommendation,
    }


def _extract_requirements(text: str, preferred: bool) -> list[str]:
    preferred_signals = ["preferred", "nice to have", "bonus", "plus", "would be helpful"]
    signals = (
        preferred_signals
        if preferred
        else ["required", "must", "need", "minimum", "responsible for", "experience with"]
    )
    requirements = []

    for raw_line in re.split(r"[\n\r]+|(?<=[.;])\s+", text):
        line = raw_line.strip(" -*\t")
        if len(line) < 12:
            continue
        lower_line = line.lower()
        if not preferred and any(signal in lower_line for signal in preferred_signals):
            continue
        if any(signal in lower_line for signal in signals):
            requirements.append(line)

    return requirements[:12]


def _extract_job_title(text: str) -> str:
    label_patterns = [
        r"(?im)^\s*project\s+role\s*:?\s*(.+?)\s{2,}",
        r"(?im)^\s*project\s+role\s*:?\s*(.+)$",
        r"(?im)^\s*job\s+title\s*:?\s*(.+)$",
        r"(?im)^\s*role\s*:?\s*(.+)$",
        r"(?im)^\s*position\s*:?\s*(.+)$",
    ]

    for pattern in label_patterns:
        match = re.search(pattern, text)
        if match:
            return _clean_metadata_value(match.group(1))

    lines = _candidate_metadata_lines(text)
    if lines and _looks_like_role_title(lines[0]):
        return _clean_metadata_value(lines[0])

    return ""


def _extract_company(text: str) -> str:
    label_patterns = [
        r"(?im)^\s*company\s*:?\s*(.+)$",
        r"(?im)^\s*organization\s*:?\s*(.+)$",
        r"(?im)^\s*employer\s*:?\s*(.+)$",
        r"(?im)^\s*client\s*:?\s*(.+)$",
    ]

    for pattern in label_patterns:
        match = re.search(pattern, text)
        if match:
            return _clean_metadata_value(match.group(1))

    lines = _candidate_metadata_lines(text)
    if len(lines) >= 2 and _looks_like_role_title(lines[0]) and _looks_like_company(lines[1]):
        return _clean_metadata_value(lines[1])

    return ""


def _candidate_metadata_lines(text: str) -> list[str]:
    blocked_prefixes = (
        "about ",
        "summary",
        "responsibilities",
        "roles ",
        "required ",
        "requirements",
        "professional ",
        "technical ",
        "additional ",
        "education",
        "minimum ",
        "must ",
        "good ",
    )
    lines = []

    for raw_line in text.splitlines():
        line = raw_line.strip(" \t-*")
        if not line:
            continue
        if len(line) > 90:
            continue
        lower_line = line.lower()
        if any(lower_line.startswith(prefix) for prefix in blocked_prefixes):
            continue
        lines.append(line)

    return lines[:8]


def _looks_like_role_title(value: str) -> bool:
    lower_value = value.lower()
    role_words = [
        "engineer",
        "analyst",
        "developer",
        "scientist",
        "architect",
        "manager",
        "consultant",
        "specialist",
        "administrator",
    ]
    return any(word in lower_value for word in role_words) and len(value.split()) <= 8


def _looks_like_company(value: str) -> bool:
    lower_value = value.lower()
    if _looks_like_role_title(value):
        return False
    blocked_words = ["hybrid", "remote", "salary", "required", "minimum", "qualification"]
    if any(word in lower_value for word in blocked_words):
        return False
    return 1 <= len(value.split()) <= 8


def _clean_metadata_value(value: str) -> str:
    cleaned = re.split(r"\s{2,}|[|•]|\t", value.strip())[0]
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" :-")
    return cleaned[:120]
