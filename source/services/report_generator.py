from datetime import datetime

from source.ui.components import bullet_text, clean_value


def generate_text_report(result: dict) -> str:
    job = result.get("job_details", {})
    scores = result.get("scores", {})
    summary = result.get("match_summary", {})

    lines = []

    lines.append("TruthFit Resume AI - Analysis Report")
    lines.append("=" * 55)
    lines.append(f"Generated At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    lines.append("Job Details")
    lines.append("-" * 55)
    for key, value in job.items():
        text = bullet_text(value)
        if text:
            lines.append(f"{key.replace('_', ' ').title()}: {text}")
    lines.append("")

    lines.append("Scores")
    lines.append("-" * 55)
    for key, value in scores.items():
        lines.append(f"{key.replace('_', ' ').title()}: {clean_value(value)}")
    lines.append("")

    lines.append("Recommendation")
    lines.append("-" * 55)
    lines.append(f"Headline: {bullet_text(summary.get('headline', ''))}")
    lines.append(f"Recommendation: {bullet_text(summary.get('apply_recommendation', ''))}")
    lines.append(f"Explanation: {bullet_text(summary.get('short_explanation', ''))}")
    lines.append("")

    lines.append("Top Strengths")
    lines.append("-" * 55)
    for item in summary.get("top_strengths", []):
        lines.append(f"- {bullet_text(item)}")
    lines.append("")

    lines.append("Top Concerns")
    lines.append("-" * 55)
    for item in summary.get("top_concerns", []):
        lines.append(f"- {bullet_text(item)}")
    lines.append("")

    lines.append("Recommended Next Actions")
    lines.append("-" * 55)
    for risk in result.get("eligibility_risks", [])[:3]:
        action = bullet_text(risk.get("recommendation", ""))
        reason = bullet_text(risk.get("risk_type", ""))
        priority = bullet_text(risk.get("severity", ""))

        if action:
            if action.startswith("- "):
                lines.extend(action.splitlines())
            else:
                lines.append(f"- Action: {action}")
        if reason and "reason:" not in action.lower():
            lines.append(f"  Reason: {reason}")
        if priority:
            lines.append(f"  Priority: {priority}")

    for fix in result.get("resume_fix_suggestions", [])[:5]:
        issue = bullet_text(fix.get("issue", ""))
        suggested_fix = bullet_text(fix.get("suggested_fix", ""))
        priority = bullet_text(fix.get("priority", ""))

        if suggested_fix:
            if suggested_fix.startswith("- "):
                lines.extend(suggested_fix.splitlines())
            else:
                lines.append(f"- Fix: {suggested_fix}")
        if issue:
            lines.append(f"  Issue: {issue}")
        if priority:
            lines.append(f"  Priority: {priority}")

    lines.append("")
    lines.append("Project Suggestions")
    lines.append("-" * 55)
    for project in result.get("project_suggestions", [])[:5]:
        title = bullet_text(project.get("project_title", ""))
        target_gap = bullet_text(project.get("target_gap", ""))
        scope = bullet_text(project.get("suggested_scope", ""))
        priority = bullet_text(project.get("priority", ""))

        if title:
            lines.append(f"- {title}")
        if target_gap:
            lines.append(f"  Gap: {target_gap}")
        if scope:
            lines.append(f"  Scope: {scope}")
        if priority:
            lines.append(f"  Priority: {priority}")

    lines.append("")
    lines.append("Certification Suggestions")
    lines.append("-" * 55)
    for cert in result.get("certification_suggestions", [])[:5]:
        name = bullet_text(cert.get("certification", ""))
        target_gap = bullet_text(cert.get("target_gap", ""))
        effort = bullet_text(cert.get("estimated_effort", ""))
        priority = bullet_text(cert.get("priority", ""))

        if name:
            lines.append(f"- {name}")
        if target_gap:
            lines.append(f"  Gap: {target_gap}")
        if effort:
            lines.append(f"  Effort: {effort}")
        if priority:
            lines.append(f"  Priority: {priority}")

    return "\n".join(lines)


def _pdf_escape(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
        .replace("\r", "")
    )


def _wrap_text(text: str, max_chars: int = 92) -> list[str]:
    wrapped = []

    for raw_line in text.splitlines():
        line = raw_line.rstrip()

        if not line:
            wrapped.append("")
            continue

        while len(line) > max_chars:
            split_at = line.rfind(" ", 0, max_chars)

            if split_at <= 0:
                split_at = max_chars

            wrapped.append(line[:split_at].rstrip())
            line = line[split_at:].lstrip()

        wrapped.append(line)

    return wrapped


def _content_stream(lines: list[str], page_number: int) -> bytes:
    commands = [
        "BT",
        "/F1 10 Tf",
        "14 TL",
        "50 760 Td",
    ]

    for line in lines:
        safe_line = _pdf_escape(line)
        commands.append(f"({safe_line}) Tj")
        commands.append("T*")

    commands.extend(
        [
            "ET",
            "BT",
            "/F1 9 Tf",
            "50 32 Td",
            f"(Page {page_number}) Tj",
            "ET",
        ]
    )

    return "\n".join(commands).encode("latin-1", errors="replace")


def generate_pdf_report(result: dict) -> bytes:
    lines = _wrap_text(generate_text_report(result))
    lines_per_page = 50
    pages = [lines[idx:idx + lines_per_page] for idx in range(0, len(lines), lines_per_page)]

    if not pages:
        pages = [["TruthFit Resume AI - Analysis Report"]]

    objects: list[bytes] = []
    page_refs = []

    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(b"")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    for page_idx, page_lines in enumerate(pages, start=1):
        page_obj_num = len(objects) + 1
        content_obj_num = page_obj_num + 1
        page_refs.append(f"{page_obj_num} 0 R")

        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content_obj_num} 0 R >>".encode("latin-1")
        )

        stream = _content_stream(page_lines, page_idx)
        objects.append(
            b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n"
            + stream
            + b"\nendstream"
        )

    objects[1] = f"<< /Type /Pages /Kids [{' '.join(page_refs)}] /Count {len(pages)} >>".encode("latin-1")

    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]

    for obj_num, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{obj_num} 0 obj\n".encode("ascii"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")

    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")

    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))

    pdf.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )

    return bytes(pdf)
