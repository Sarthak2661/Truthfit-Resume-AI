import html
import re
import textwrap
from collections import Counter
from uuid import uuid4

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st


# -------------------------------------------------
# Basic helpers
# -------------------------------------------------

def unique_chart_key(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


def render_html(markup: str):
    cleaned_markup = textwrap.dedent(markup).strip()

    if hasattr(st, "html"):
        st.html(cleaned_markup)
    else:
        st.markdown(cleaned_markup, unsafe_allow_html=True)


def clean_value(value) -> str:
    if value is None:
        return ""

    if isinstance(value, list):
        return "\n".join([f"- {clean_value(v)}" for v in value if clean_value(v)])

    if isinstance(value, dict):
        return "\n".join(
            [
                f"{str(k).replace('_', ' ').title()}: {clean_value(v)}"
                for k, v in value.items()
                if clean_value(v)
            ]
        )

    text = str(value)
    text = text.replace('\\"', '"').replace("\\'", "'")
    text = text.replace("\\n", "\n").replace("\\/", "/")

    for _ in range(3):
        unescaped = html.unescape(text)
        if unescaped == text:
            break
        text = unescaped

    text = re.sub(r"```(?:html|json|text|markdown)?", "", text, flags=re.IGNORECASE)
    text = text.replace("```", "")
    text = re.sub(r"<\s*summary[^>]*>", "Summary: ", text, flags=re.IGNORECASE)
    text = re.sub(r"</\s*summary\s*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<\s*li[^>]*>", "- ", text, flags=re.IGNORECASE)
    text = re.sub(r"</\s*li\s*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<\s*br\s*/?\s*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</\s*(div|p|tr|h[1-6]|details|ul|ol)\s*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("`", "")

    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"\b[Aa]sk user\b", "Ask the candidate", text)
    text = re.sub(r"\b[Aa]sk the user\b", "Ask the candidate", text)
    text = re.sub(r"\b[Tt]he user\b", "the candidate", text)
    text = re.sub(r"\b[Uu]ser\b", "candidate", text)

    return text.strip()


def normalize_analysis_result(value):
    if isinstance(value, dict):
        return {key: normalize_analysis_result(item) for key, item in value.items()}

    if isinstance(value, list):
        return [normalize_analysis_result(item) for item in value]

    if isinstance(value, str):
        return clean_value(value)

    return value


def bullet_text(value) -> str:
    text = clean_value(value)

    if not text:
        return ""

    lines = [line.strip() for line in text.splitlines() if line.strip()]

    if len(lines) > 1:
        normalized = []
        for line in lines:
            if line.startswith("- "):
                normalized.append(f"- {line[2:].strip()}")
            else:
                normalized.append(f"- {line}")
        return "\n".join(normalized)

    return lines[0] if lines else ""


def display_text(value) -> str:
    return bullet_text(value) or clean_value(value)


def friendly_label(value) -> str:
    text = clean_value(value)
    mapping = {
        "High": "Important",
        "Medium": "Would help",
        "Low": "Nice to have",
        "high": "Important",
        "medium": "Would help",
        "low": "Nice to have",
        "Partial": "Needs proof",
        "Unsafe": "Do not claim",
        "Missing": "Missing",
        "Supported": "Supported",
        "Covered": "Covered",
        "Strong": "Strong",
        "Weak": "Weak",
        "Good Match": "Good Match",
        "Strong Match": "Strong Match",
        "Partial Match": "Partial Match",
        "Weak Match": "Weak Match",
    }
    return mapping.get(text, text)


def display_field_value(label: str, value) -> str:
    if label.lower() in [
        "priority",
        "action level",
        "severity",
        "attention",
        "status",
        "coverage status",
        "evidence status",
        "match strength",
    ]:
        return friendly_label(value)
    return display_text(value)


def friendly_field_label(label: str) -> str:
    mapping = {
        "Priority": "Action Level",
        "Severity": "Attention",
        "Resume Evidence": "Profile Evidence",
        "Jd Evidence": "JD Evidence",
        "Why It Helps": "Why This Helps",
        "Why Needed": "Why This Matters",
    }
    return mapping.get(label, label)


def text_to_html(value) -> str:
    text = display_text(value)

    if not text:
        return ""

    lines = [line.strip() for line in text.splitlines() if line.strip()]

    if len(lines) > 1 or any(line.startswith("- ") for line in lines):
        return "<ul>" + "".join(
            f"<li>{html.escape(line[2:] if line.startswith('- ') else line)}</li>"
            for line in lines
        ) + "</ul>"

    return html.escape(text)


# -------------------------------------------------
# Status / score helpers
# -------------------------------------------------

def status_to_chip_class(status: str) -> str:
    status = (status or "").lower()

    if status in [
        "supported",
        "covered",
        "strong",
        "strong match",
        "low",
        "nice to have",
        "apply confidently",
    ]:
        return "chip-green"

    if status in [
        "partial",
        "needs proof",
        "good match",
        "medium",
        "would help",
        "apply after tailoring",
    ]:
        return "chip-yellow"

    if status in [
        "missing",
        "unsafe",
        "weak",
        "weak match",
        "high",
        "important",
        "skip",
        "high risk",
        "important risk",
    ]:
        return "chip-red"

    return "chip-blue"


def severity_rank(status: str) -> int:
    status = (status or "").lower()

    if status in ["high", "important", "missing", "unsafe", "weak"]:
        return 0

    if status in ["medium", "would help", "partial", "needs proof"]:
        return 1

    if status in ["low", "nice to have", "supported", "covered", "strong"]:
        return 2

    return 3


def get_score_label(score: int) -> str:
    if score >= 85:
        return "Strong Match"
    if score >= 70:
        return "Good Match"
    if score >= 50:
        return "Partial Match"
    return "Weak Match"


def get_score_meaning(score: int) -> str:
    if score >= 85:
        return "Apply confidently"
    if score >= 70:
        return "Apply after tailoring"
    if score >= 50:
        return "Improve resume first"
    return "The skill gap is high"


def get_score_class(score: int) -> str:
    if score >= 85:
        return "score-strong"
    if score >= 70:
        return "score-good"
    if score >= 50:
        return "score-partial"
    return "score-weak"


# -------------------------------------------------
# Chart helpers
# -------------------------------------------------

def is_dark_theme() -> bool:
    return st.session_state.get("theme", "Dark") == "Dark"


def chart_template() -> str:
    return "plotly_dark" if is_dark_theme() else "plotly_white"


def chart_palette() -> dict:
    return {
        "Covered": "#22C55E",
        "Supported": "#22C55E",
        "Strong": "#22C55E",
        "Strong Match": "#22C55E",
        "Partial": "#F59E0B",
        "Good Match": "#14B8A6",
        "Medium": "#F59E0B",
        "Would help": "#F59E0B",
        "Needs proof": "#F59E0B",
        "Missing": "#EF4444",
        "Unsafe": "#EF4444",
        "Weak": "#EF4444",
        "Weak Match": "#EF4444",
        "High": "#EF4444",
        "Important": "#EF4444",
        "Low": "#22C55E",
        "Nice to have": "#22C55E",
        "Unknown": "#64748B",
    }


def apply_chart_layout(fig, height: int, title: str = ""):
    font_color = "#E5E7EB" if is_dark_theme() else "#0F172A"
    grid_color = "rgba(148,163,184,0.22)" if is_dark_theme() else "rgba(15,23,42,0.12)"

    fig.update_layout(
        title=title,
        height=height,
        template=chart_template(),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=font_color),
        margin=dict(l=24, r=24, t=54 if title else 24, b=34),
    )

    fig.update_xaxes(gridcolor=grid_color, zerolinecolor=grid_color)
    fig.update_yaxes(gridcolor=grid_color, zerolinecolor=grid_color)

    return fig


# -------------------------------------------------
# Page / navbar
# -------------------------------------------------

def render_page_header(title: str, subtitle: str = ""):
    render_html(
        f"""
        <div class="page-header">
            <h1>{html.escape(title)}</h1>
            <p>{html.escape(subtitle)}</p>
        </div>
        """
    )


def render_section_kicker(title: str):
    render_html(
        f"""
        <div class="section-kicker">
            {html.escape(title)}
        </div>
        """
    )


def render_navbar():
    render_html(
        """
        <div class="truthfit-navbar">
            <div>
                <div class="truthfit-brand">TruthFit <span>Resume AI</span></div>
                <div class="nav-subtitle">Resume and job-fit review</div>
            </div>
        </div>
        """
    )


# -------------------------------------------------
# Home page
# -------------------------------------------------

def render_feature_card(title: str, body: str):
    render_html(
        f"""
        <div class="tf-card feature-card">
            <h3>{html.escape(title)}</h3>
            <p>{html.escape(body)}</p>
        </div>
        """
    )


def render_homepage():
    render_html(
        """
        <div class="hero hero-split">
            <div class="hero-copy">
                <div class="mini-label">Resume checker and job-fit dashboard</div>
                <h1>See where your resume fits, <span class="gradient-text">and what to fix next.</span></h1>
                <p>
                    Upload a resume, paste a job description, and get a practical match review:
                    keyword coverage, skill gaps, eligibility notes, and rewrite ideas grounded in
                    experience already on the resume.
                </p>
                <div class="hero-metrics">
                    <div><strong>5</strong><span>fit scores</span></div>
                    <div><strong>ATS</strong><span>keyword map</span></div>
                    <div><strong>0</strong><span>unsupported claims</span></div>
                </div>
            </div>

            <div class="hero-visual" aria-label="Resume analysis preview">
                <div class="resume-sheet">
                    <div class="sheet-top"></div>
                    <div class="sheet-line wide"></div>
                    <div class="sheet-line"></div>
                    <div class="sheet-line short"></div>
                    <div class="sheet-section">
                        <span></span><span></span><span></span>
                    </div>
                    <div class="sheet-line wide"></div>
                    <div class="sheet-line"></div>
                    <div class="sheet-line short"></div>
                </div>

                <div class="ai-panel">
                    <div class="ai-ring">82</div>
                    <div>
                        <strong>Good Match</strong>
                        <span>Keyword and risk review</span>
                    </div>
                </div>

                <div class="keyword-strip">
                    <span>Covered</span>
                    <span>Needs proof</span>
                    <span>Missing</span>
                </div>
            </div>
        </div>
        """
    )

    st.write("")

    c1, c2, c3 = st.columns(3, gap="large")

    with c1:
        render_feature_card(
            "Upload",
            "Read PDF, DOCX, or TXT resumes and preview extracted content before analysis."
        )

    with c2:
        render_feature_card(
            "Compare",
            "Map resume evidence against job requirements, keywords, and eligibility signals."
        )

    with c3:
        render_feature_card(
            "Improve",
            "Get visual scores, careful rewrites, and a focused skill-gap learning plan."
        )

    st.write("")

    render_html(
        """
        <div class="process-band">
            <div>
                <span class="step-dot">1</span>
                <h3>Keyword Coverage</h3>
                <p>Shows covered, needs-proof, and missing terms without overwhelming tables.</p>
            </div>
            <div>
                <span class="step-dot">2</span>
                <h3>Evidence Check</h3>
                <p>Flags claims that need stronger support before they go on a resume.</p>
            </div>
            <div>
                <span class="step-dot">3</span>
                <h3>Action Plan</h3>
                <p>Turns gaps into specific resume fixes and learning steps.</p>
            </div>
        </div>
        """
    )


# -------------------------------------------------
# Dashboard cards
# -------------------------------------------------

def render_score_card(title: str, score: int):
    score = int(score or 0)
    label = get_score_label(score)
    meaning = get_score_meaning(score)
    css_class = get_score_class(score)

    render_html(
        f"""
        <div class="score-card {css_class}">
            <div class="mini-label">{html.escape(title)}</div>
            <div class="score-value">{score}<span>/100</span></div>
            <div class="score-label">{html.escape(label)}</div>
            <p>{html.escape(meaning)}</p>
        </div>
        """
    )

    st.progress(score / 100)


def render_summary_card(title: str, value: str, subtitle: str = ""):
    render_html(
        f"""
        <div class="summary-card">
            <div class="mini-label">{html.escape(title)}</div>
            <h3>{html.escape(clean_value(value or "Not specified"))}</h3>
            <p>{html.escape(clean_value(subtitle or ""))}</p>
        </div>
        """
    )


def render_verdict_card(result: dict):
    job = result.get("job_details", {})
    scores = result.get("scores", {})
    summary = result.get("match_summary", {})
    risks = result.get("eligibility_risks", [])
    red_flags = result.get("jd_red_flags", [])

    overall_score = int(scores.get("overall_match_score", 0) or 0)
    recommendation = clean_value(summary.get("apply_recommendation", "Review before applying"))
    explanation = clean_value(summary.get("short_explanation", ""))
    job_title = clean_value(job.get("job_title", "Target Role"))
    company = clean_value(job.get("company_name", "Target Company"))

    high_risk_count = sum(
        1 for item in risks + red_flags
        if clean_value(item.get("severity", "")).lower() == "high"
    )

    risk_label = "Important Risk" if high_risk_count else "Needs Review"

    if overall_score >= 85 and not high_risk_count:
        risk_label = "Ready To Apply"

    chip_class = status_to_chip_class(risk_label)

    render_html(
        f"""
        <div class="verdict-card">
            <div>
                <div class="mini-label">Final Verdict</div>
                <h2>{html.escape(recommendation)}</h2>
                <p>{html.escape(explanation)}</p>
            </div>

            <div class="verdict-side">
                <span class="chip {chip_class}">{html.escape(risk_label)}</span>
                <strong>{overall_score}/100</strong>
                <span>{html.escape(job_title)} at {html.escape(company)}</span>
            </div>
        </div>
        """
    )


def render_recommendation_card(summary: dict):
    recommendation = clean_value(summary.get("apply_recommendation", ""))
    explanation = clean_value(summary.get("short_explanation", ""))

    render_html(
        f"""
        <div class="tf-card recommendation-detail">
            <div class="mini-label">Recommendation</div>
            <h3>{html.escape(recommendation)}</h3>
            <p>{html.escape(explanation)}</p>
        </div>
        """
    )


def render_analysis_disclaimer():
    render_html(
        """
        <div class="tf-card">
            <div class="mini-label">Accuracy Note</div>
            <p>
                This analysis is AI-assisted and may be incomplete. Use it as a resume review aid,
                not as a hiring decision or guaranteed ATS result.
            </p>
        </div>
        """
    )


def render_confidence_findings(findings: list, max_items: int = 5):
    st.markdown(
        '<div class="section-title">Confidence and Evidence Check</div>',
        unsafe_allow_html=True
    )

    if not findings:
        st.info("No confidence findings returned.")
        return

    cards_html = ""

    for idx, item in enumerate(findings[:max_items], start=1):
        if not isinstance(item, dict):
            continue

        finding = clean_value(item.get("finding", f"Finding {idx}"))
        confidence = clean_value(item.get("confidence", "Medium"))
        risk = clean_value(item.get("risk", "Medium"))
        resume_evidence = clean_value(item.get("resume_evidence", "")) or "Not found in resume."
        jd_evidence = clean_value(item.get("jd_evidence", "")) or "Not found in job description."
        recommendation = clean_value(item.get("recommendation", "Review manually before using this advice."))
        verify_manually = clean_value(item.get("verify_manually", "Confirm this before editing the resume."))
        chip_class = status_to_chip_class(risk)
        confidence_display = confidence.title()
        risk_display = risk.title()

        cards_html += f"""
        <div class="modern-info-card">
            <div class="modern-card-head">
                <h4>{html.escape(finding)}</h4>
                <span class="chip {chip_class}">{html.escape(risk_display)} Risk</span>
            </div>
            <div class="modern-info-row">
                <span>Confidence</span>
                <div>{html.escape(confidence_display)}</div>
            </div>
            <details class="evidence-detail">
                <summary>Resume evidence</summary>
                <div class="modern-info-row">
                    <div>{html.escape(resume_evidence)}</div>
                </div>
            </details>
            <details class="evidence-detail">
                <summary>JD evidence</summary>
                <div class="modern-info-row">
                    <div>{html.escape(jd_evidence)}</div>
                </div>
            </details>
            <div class="modern-info-row">
                <span>Recommendation</span>
                <div>{html.escape(recommendation)}</div>
            </div>
            <div class="modern-info-row">
                <span>Verify Manually</span>
                <div>{html.escape(verify_manually)}</div>
            </div>
        </div>
        """

    render_html(f'<div class="card-grid">{cards_html}</div>')

    if len(findings) > max_items:
        with st.expander(f"Show {len(findings) - max_items} more confidence findings"):
            for item in findings[max_items:]:
                st.json(item)


def render_fix_impact_matrix(fixes: list, max_items: int = 5):
    st.markdown(
        '<div class="section-title">Top Fixes by Impact and Effort</div>',
        unsafe_allow_html=True
    )

    if not fixes:
        st.info("No fix impact matrix returned.")
        return

    rows = []

    for item in fixes[:max_items]:
        if not isinstance(item, dict):
            continue

        rows.append(
            {
                "Fix": clean_value(item.get("fix", "")),
                "Impact": clean_value(item.get("impact", "")),
                "Effort": clean_value(item.get("effort", "")),
                "Priority": friendly_label(item.get("priority", "")),
                "Why it matters": clean_value(item.get("why_it_matters", "")),
                "Source": clean_value(item.get("source", "")),
            }
        )

    if not rows:
        st.info("No fix impact matrix returned.")
        return

    st.dataframe(
        pd.DataFrame(rows),
        width="stretch",
        hide_index=True,
        column_config={
            "Why it matters": st.column_config.TextColumn("Why it matters", width="large"),
            "Fix": st.column_config.TextColumn("Fix", width="medium"),
        },
    )


def render_skill_match_table(skills: dict, ats_keywords: list):
    st.markdown(
        '<div class="section-title">Matched vs Missing Skills</div>',
        unsafe_allow_html=True
    )

    rows = []

    keyword_lookup = {}
    for item in ats_keywords:
        if isinstance(item, dict):
            keyword_lookup[clean_value(item.get("keyword", "")).lower()] = item

    for item in skills.get("matched_skills", []):
        if not isinstance(item, dict):
            continue
        skill = clean_value(item.get("skill", ""))
        keyword = keyword_lookup.get(skill.lower(), {})
        rows.append(
            {
                "Skill": skill,
                "Status": friendly_label(item.get("evidence_status", "Supported")),
                "Importance": friendly_label(keyword.get("importance", "Important")),
                "Resume Evidence": clean_value(item.get("resume_evidence", "")) or "Not found in resume.",
                "Action": "Keep visible in summary, skills, or project bullets.",
            }
        )

    for item in skills.get("missing_skills", []):
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "Skill": clean_value(item.get("skill", "")),
                "Status": "Missing",
                "Importance": friendly_label(item.get("priority", "")),
                "Resume Evidence": "Not found in resume.",
                "Action": clean_value(item.get("reason", "")) or "Add only after building real evidence.",
            }
        )

    for item in skills.get("nice_to_have_skills", []):
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "Skill": clean_value(item.get("skill", "")),
                "Status": friendly_label(item.get("status", "Optional")),
                "Importance": "Nice to have",
                "Resume Evidence": clean_value(item.get("resume_evidence", "")) or "Not found in resume.",
                "Action": "Optional improvement if this role emphasizes it.",
            }
        )

    if not rows:
        st.info("No skill comparison data available.")
        return

    st.dataframe(
        pd.DataFrame(rows),
        width="stretch",
        hide_index=True,
        column_config={
            "Resume Evidence": st.column_config.TextColumn("Resume Evidence", width="large"),
            "Action": st.column_config.TextColumn("Action", width="large"),
        },
    )


def render_chip_group(title: str, items: list, key_name: str = "skill", max_items: int = 20):
    st.markdown(
        f'<div class="section-title">{html.escape(title)}</div>',
        unsafe_allow_html=True
    )

    if not items:
        st.info("No items found.")
        return

    chips = ""

    for item in items[:max_items]:
        if isinstance(item, dict):
            label = (
                item.get(key_name)
                or item.get("requirement")
                or item.get("keyword")
                or ""
            )
            status = (
                item.get("evidence_status")
                or item.get("status")
                or item.get("coverage_status")
                or item.get("priority")
                or ""
            )
        else:
            label = str(item)
            status = ""

        chip_class = status_to_chip_class(status)
        chips += f'<span class="chip {chip_class}">{html.escape(clean_value(label))}</span>'

    if len(items) > max_items:
        chips += f'<span class="chip chip-blue">+{len(items) - max_items} more</span>'

    render_html(f'<div class="chip-cloud">{chips}</div>')


def render_card_grid(
    title: str,
    items: list,
    title_key: str,
    badge_key: str = "",
    body_keys: list = None,
    empty_message: str = "No data available.",
    columns: int = 2,
    max_items: int = 5
):
    st.markdown(
        f'<div class="section-title">{html.escape(title)}</div>',
        unsafe_allow_html=True
    )

    if not items:
        st.info(empty_message)
        return

    body_keys = body_keys or []
    grid_class = "card-grid card-grid-1" if columns == 1 else "card-grid"

    cards_html = ""

    sorted_items = sorted(
        items[:max_items],
        key=lambda item: severity_rank(clean_value(item.get(badge_key, ""))) if isinstance(item, dict) else 9
    )

    for idx, item in enumerate(sorted_items, start=1):
        if not isinstance(item, dict):
            card_title = f"Item {idx}"
            badge_value = ""
            body_html = f"<p>{text_to_html(item)}</p>"
        else:
            card_title = clean_value(
                item.get(title_key)
                or item.get("requirement")
                or item.get("skill")
                or item.get("keyword")
                or f"Item {idx}"
            )

            badge_value = clean_value(item.get(badge_key, "")) if badge_key else ""
            badge_display = friendly_label(badge_value)
            badge_class = status_to_chip_class(badge_value)

            body_html = ""

            for key in body_keys:
                value = item.get(key, "")

                if not clean_value(value):
                    continue

                label = friendly_field_label(key.replace("_", " ").title())
                display_value = display_field_value(label, value)
                row_content = f"""
                    <span>{html.escape(label)}</span>
                    <div>{text_to_html(display_value)}</div>
                """

                if "evidence" in label.lower():
                    body_html += f"""
                    <details class="evidence-detail">
                        <summary>{html.escape(label)}</summary>
                        <div class="modern-info-row">
                            <div>{text_to_html(display_value)}</div>
                        </div>
                    </details>
                    """
                else:
                    body_html += f"""
                    <div class="modern-info-row">
                        {row_content}
                    </div>
                    """

        badge_html = ""

        if badge_value:
            badge_html = f'<span class="chip {badge_class}">{html.escape(badge_display)}</span>'

        cards_html += f"""
        <div class="modern-info-card">
            <div class="modern-card-head">
                <h4>{html.escape(card_title)}</h4>
                {badge_html}
            </div>
            {body_html}
        </div>
        """

    render_html(f'<div class="{grid_class}">{cards_html}</div>')

    if len(items) > max_items:
        with st.expander(f"Show {len(items) - max_items} more"):
            for item in items[max_items:]:
                st.json(item)


def render_top_strengths_concerns(summary: dict):
    strengths = summary.get("top_strengths", [])
    concerns = summary.get("top_concerns", [])

    st.markdown(
        '<div class="section-title center-title">Strengths and Concerns</div>',
        unsafe_allow_html=True
    )

    left, right = st.columns(2, gap="large")

    with left:
        render_html('<div class="sub-card-title">Top Strengths</div>')

        if strengths:
            html_items = "".join(
                f'<div class="balanced-item strength-item">{text_to_html(item)}</div>'
                for item in strengths[:5]
            )
            render_html(f'<div class="balanced-stack">{html_items}</div>')
        else:
            st.success("No specific strengths returned.")

    with right:
        render_html('<div class="sub-card-title">Top Concerns</div>')

        if concerns:
            html_items = "".join(
                f'<div class="balanced-item concern-item">{text_to_html(item)}</div>'
                for item in concerns[:5]
            )
            render_html(f'<div class="balanced-stack">{html_items}</div>')
        else:
            st.success("No major concerns found.")


def render_visual_note_card():
    render_html(
        """
        <div class="visual-note-card">
            <div class="mini-label">How to read this</div>
            <h3>Focus on red and yellow first.</h3>
            <p>
                Green means the resume already supports the requirement. Yellow means the evidence exists
                but needs clearer wording. Red means the skill or requirement is missing or risky to claim.
            </p>
        </div>
        """
    )


# -------------------------------------------------
# Charts
# -------------------------------------------------

def render_score_radar(scores: dict):
    labels = ["Overall", "Technical", "ATS", "Eligibility", "Experience"]

    values = [
        int(scores.get("overall_match_score", 0) or 0),
        int(scores.get("technical_match_score", 0) or 0),
        int(scores.get("ats_keyword_coverage_score", 0) or 0),
        int(scores.get("eligibility_score", 0) or 0),
        int(scores.get("experience_match_score", 0) or 0),
    ]

    fig = go.Figure()

    fig.add_trace(
        go.Scatterpolar(
            r=values + [values[0]],
            theta=labels + [labels[0]],
            fill="toself",
            name="Match Profile",
            line=dict(color="#14B8A6"),
            fillcolor="rgba(20,184,166,0.24)"
        )
    )

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=False,
    )

    apply_chart_layout(fig, 360)

    st.plotly_chart(
        fig,
        width="stretch",
        key=unique_chart_key("score_radar")
    )


def render_score_driver_bar(result: dict):
    drivers = result.get("score_drivers", [])

    if not drivers:
        breakdown = result.get("ats_score_breakdown", [])
        drivers = [
            {
                "driver": item.get("category", ""),
                "contribution": int(item.get("score", 0) or 0),
                "direction": "Positive",
                "evidence": item.get("evidence", ""),
            }
            for item in breakdown
            if isinstance(item, dict)
        ]

    if not drivers:
        st.info("No score driver data available.")
        return

    rows = []
    for item in drivers:
        if not isinstance(item, dict):
            continue
        contribution = int(item.get("contribution", 0) or 0)
        direction = clean_value(item.get("direction", "Positive"))
        if direction.lower() == "negative" and contribution > 0:
            contribution = -contribution
        rows.append(
            {
                "Driver": clean_value(item.get("driver", "")),
                "Contribution": contribution,
                "Evidence": clean_value(item.get("evidence", "")),
                "Direction": "Gain" if contribution >= 0 else "Gap",
            }
        )

    if not rows:
        st.info("No score driver data available.")
        return

    df = pd.DataFrame(rows)
    fig = px.bar(
        df,
        x="Contribution",
        y="Driver",
        color="Direction",
        text="Contribution",
        title="What Drives the Match Score",
        color_discrete_map={"Gain": "#22C55E", "Gap": "#EF4444"},
        orientation="h",
    )
    fig.update_traces(texttemplate="%{x:+d}", textposition="outside")
    apply_chart_layout(fig, 340)
    st.plotly_chart(fig, width="stretch", key=unique_chart_key("score_drivers"))

    with st.expander("Show score driver evidence"):
        st.dataframe(
            df[["Driver", "Contribution", "Evidence"]],
            width="stretch",
            hide_index=True,
            column_config={"Evidence": st.column_config.TextColumn("Evidence", width="large")},
        )


def render_evidence_coverage_meter(result: dict):
    statuses = []

    def add_status(value):
        text = clean_value(value)
        if text:
            statuses.append(text)

    for item in result.get("ats_keyword_coverage", []):
        if isinstance(item, dict):
            add_status(item.get("coverage_status"))

    requirements = result.get("jd_requirements", {})
    for group_name in ["must_have", "nice_to_have", "job_title_requirements"]:
        for item in requirements.get(group_name, []):
            if isinstance(item, dict):
                add_status(item.get("status"))

    for item in result.get("evidence_based_matches", []):
        if isinstance(item, dict):
            add_status(item.get("match_strength"))

    for item in result.get("hallucination_guardrail", []):
        if isinstance(item, dict):
            add_status(item.get("status"))

    for item in result.get("before_after_bullets", []):
        if isinstance(item, dict):
            add_status(item.get("evidence_status"))

    buckets = {"Supported": 0, "Partial": 0, "Missing": 0, "Unsafe": 0}

    for status in statuses:
        normalized = status.lower()
        if normalized in ["supported", "covered", "strong"]:
            buckets["Supported"] += 1
        elif normalized in ["partial", "needs proof"]:
            buckets["Partial"] += 1
        elif normalized in ["missing", "weak"]:
            buckets["Missing"] += 1
        elif normalized == "unsafe":
            buckets["Unsafe"] += 1

    if not any(buckets.values()):
        st.info("No evidence coverage data available.")
        return

    cols = st.columns(4, gap="small")
    meta = [
        ("Supported claims", "Supported", "Supported by resume or JD evidence"),
        ("Partial claims", "Partial", "Needs clearer evidence"),
        ("Missing claims", "Missing", "Not found in resume"),
        ("Unsafe claims", "Unsafe", "Do not claim without proof"),
    ]

    for col, (title, key, subtitle) in zip(cols, meta):
        with col:
            render_summary_card(title, str(buckets[key]), subtitle)


def render_ats_donut(ats_keywords: list):
    if not ats_keywords:
        st.info("No ATS keyword data available.")
        return

    counts = Counter(friendly_label(item.get("coverage_status", "Unknown")) for item in ats_keywords)

    labels = list(counts.keys())
    values = list(counts.values())
    colors = [chart_palette().get(label, "#64748B") for label in labels]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.58,
                marker=dict(colors=colors),
                textinfo="label+percent",
                sort=False,
            )
        ]
    )

    apply_chart_layout(fig, 340, "ATS Keyword Coverage")

    st.plotly_chart(
        fig,
        width="stretch",
        key=unique_chart_key("ats_donut")
    )


def render_requirement_status_bar(requirements: dict):
    records = []

    for group_name in ["must_have", "nice_to_have", "job_title_requirements"]:
        for item in requirements.get(group_name, []):
            records.append(
                {
                    "Group": group_name.replace("_", " ").title(),
                    "Status": item.get("status", "Unknown")
                }
            )

    if not records:
        st.info("No requirement status data available.")
        return

    df = pd.DataFrame(records)
    grouped = df.groupby(["Group", "Status"]).size().reset_index(name="Count")

    fig = px.bar(
        grouped,
        x="Count",
        y="Group",
        color="Status",
        barmode="stack",
        text="Count",
        title="Requirement Coverage by Category",
        color_discrete_map=chart_palette(),
        orientation="h",
    )

    fig.update_traces(textposition="inside")
    apply_chart_layout(fig, 340)

    st.plotly_chart(
        fig,
        width="stretch",
        key=unique_chart_key("requirement_status_bar")
    )


def render_missing_skill_priority_chart(missing_skills: list):
    if not missing_skills:
        st.success("No missing skills detected.")
        return

    df = pd.DataFrame(missing_skills)

    if "priority" not in df.columns:
        st.info("Missing skill priority data unavailable.")
        return

    priority_order = {
        "High": 0,
        "Important": 0,
        "high": 0,
        "important": 0,
        "Medium": 1,
        "Would help": 1,
        "medium": 1,
        "would help": 1,
        "Low": 2,
        "Nice to have": 2,
        "low": 2,
        "nice to have": 2,
    }

    grouped = df.groupby("priority").size().reset_index(name="Count")
    grouped["sort_order"] = grouped["priority"].map(priority_order).fillna(3)
    grouped = grouped.sort_values(["sort_order", "priority"])
    grouped["Priority"] = grouped["priority"].apply(friendly_label)

    fig = px.bar(
        grouped,
        x="Count",
        y="Priority",
        text="Count",
        title="Missing Skills by Action Level",
        color="Priority",
        color_discrete_map=chart_palette(),
        orientation="h",
    )

    fig.update_traces(textposition="outside")
    apply_chart_layout(fig, 300)

    st.plotly_chart(
        fig,
        width="stretch",
        key=unique_chart_key("missing_skill_priority")
    )


# -------------------------------------------------
# ATS checklist
# -------------------------------------------------

def render_keyword_checklist(ats_keywords: list):
    if not ats_keywords:
        st.info("No ATS keyword data available.")
        return

    df = pd.DataFrame(ats_keywords)

    if df.empty or "coverage_status" not in df.columns or "keyword" not in df.columns:
        st.info("Keyword checklist data unavailable.")
        return

    status_order = {"Missing": 0, "Needs proof": 1, "Partial": 1, "Covered": 2}
    importance_order = {
        "High": 0,
        "Important": 0,
        "high": 0,
        "important": 0,
        "Medium": 1,
        "Would help": 1,
        "medium": 1,
        "would help": 1,
        "Low": 2,
        "Nice to have": 2,
        "low": 2,
        "nice to have": 2,
    }

    df["status_sort"] = df["coverage_status"].map(status_order).fillna(3)
    df["importance_sort"] = df["importance"].map(importance_order).fillna(3)
    df = df.sort_values(["status_sort", "importance_sort", "keyword"]).head(18)

    rows_html = ""

    for _, row in df.iterrows():
        status = clean_value(row.get("coverage_status", "Unknown"))
        keyword = clean_value(row.get("keyword", "Keyword"))
        importance = clean_value(row.get("importance", ""))
        evidence = clean_value(row.get("resume_evidence", "")) or "No resume evidence returned."
        chip_class = status_to_chip_class(status)

        rows_html += f"""
        <div class="keyword-card">
            <div class="keyword-card-top">
                <h4>{html.escape(keyword)}</h4>
                <div class="keyword-badges">
                    <span class="chip {chip_class}">{html.escape(friendly_label(status))}</span>
                    <span class="priority-badge">{html.escape(friendly_label(importance))}</span>
                </div>
            </div>
            <p>{html.escape(evidence)}</p>
        </div>
        """

    render_html(
        f"""
        <div class="ats-checklist-card">
            <div class="section-title no-top-margin">ATS Keyword Checklist</div>
            <div class="keyword-grid">
                {rows_html}
            </div>
        </div>
        """
    )


# -------------------------------------------------
# Risk / evidence / rewrite / action cards
# -------------------------------------------------

def render_risk_cards(risks: list):
    st.markdown(
        '<div class="section-title">Eligibility Risk Detector</div>',
        unsafe_allow_html=True
    )

    if not risks:
        st.success("No major eligibility risks detected.")
        return

    cards_html = ""

    sorted_risks = sorted(
        risks,
        key=lambda item: severity_rank(clean_value(item.get("severity", "")))
    )

    for risk in sorted_risks:
        risk_type = clean_value(risk.get("risk_type", "Risk"))
        severity = clean_value(risk.get("severity", "Medium"))
        explanation = clean_value(risk.get("explanation", ""))
        recommendation = clean_value(risk.get("recommendation", ""))
        jd_evidence = clean_value(risk.get("jd_evidence", ""))
        resume_evidence = clean_value(risk.get("resume_evidence", ""))
        chip_class = status_to_chip_class(severity)

        evidence_html = ""

        if jd_evidence or resume_evidence:
            evidence_html = f"""
            <details>
                <summary>Show evidence</summary>
                <div class="modern-info-row">
                    <span>JD Evidence</span>
                    <div>{html.escape(jd_evidence)}</div>
                </div>
                <div class="modern-info-row">
                    <span>Resume Evidence</span>
                    <div>{html.escape(resume_evidence)}</div>
                </div>
            </details>
            """

        cards_html += f"""
        <div class="modern-info-card risk-card">
            <div class="modern-card-head">
                <h4>{html.escape(risk_type)}</h4>
                <span class="chip {chip_class}">{html.escape(friendly_label(severity))}</span>
            </div>
            <div class="modern-info-row">
                <span>Explanation</span>
                <div>{html.escape(explanation)}</div>
            </div>
            <div class="modern-info-row">
                <span>Recommendation</span>
                <div>{html.escape(recommendation)}</div>
            </div>
            {evidence_html}
        </div>
        """

    render_html(f'<div class="card-grid">{cards_html}</div>')


def render_evidence_cards(matches: list, max_items: int = 5):
    st.markdown(
        '<div class="section-title">Evidence-Based Matching</div>',
        unsafe_allow_html=True
    )

    if not matches:
        st.info("No evidence matches available.")
        return

    cards_html = ""

    for idx, item in enumerate(matches[:max_items], start=1):
        requirement = clean_value(item.get("jd_requirement", f"Match {idx}"))
        strength = clean_value(item.get("match_strength", "Partial"))
        explanation = clean_value(item.get("explanation", ""))
        evidence = clean_value(item.get("resume_evidence", ""))
        chip_class = status_to_chip_class(strength)

        cards_html += f"""
        <div class="modern-info-card evidence-card">
            <div class="modern-card-head">
                <h4>{html.escape(requirement)}</h4>
                <span class="chip {chip_class}">{html.escape(friendly_label(strength))}</span>
            </div>
            <div class="modern-info-row">
                <span>Explanation</span>
                <div>{html.escape(explanation)}</div>
            </div>
            <details>
                <summary>Resume evidence</summary>
                <p>{html.escape(evidence)}</p>
            </details>
        </div>
        """

    render_html(f'<div class="card-grid card-grid-1">{cards_html}</div>')

    if len(matches) > max_items:
        with st.expander(f"Show {len(matches) - max_items} more"):
            for item in matches[max_items:]:
                st.json(item)


def render_bullet_comparison(bullets: list, max_items: int = 5):
    st.markdown(
        '<div class="section-title">Before vs After Bullet Comparison</div>',
        unsafe_allow_html=True
    )

    if not bullets:
        st.info("No bullet rewrites available.")
        return

    cards_html = ""

    for idx, bullet in enumerate(bullets[:max_items], start=1):
        status = clean_value(bullet.get("evidence_status", ""))
        before_text = clean_value(bullet.get("original", ""))
        after_text = clean_value(bullet.get("rewritten", ""))
        why_text = clean_value(bullet.get("why_improved", ""))
        risk_note = clean_value(bullet.get("risk_note", ""))
        chip_class = status_to_chip_class(status)

        risk_html = ""

        if risk_note:
            risk_html = f"""
            <div class="modern-info-row">
                <span>Risk Note</span>
                <div>{html.escape(risk_note)}</div>
            </div>
            """

        cards_html += f"""
        <div class="modern-info-card rewrite-card">
            <div class="modern-card-head">
                <h4>Bullet {idx}</h4>
                <span class="chip {chip_class}">{html.escape(friendly_label(status))}</span>
            </div>
            <div class="compare-grid">
                <div>
                    <span>Before</span>
                    <p>{html.escape(before_text)}</p>
                </div>
                <div>
                    <span>After</span>
                    <p>{html.escape(after_text)}</p>
                </div>
            </div>
            <div class="modern-info-row">
                <span>Why Improved</span>
                <div>{html.escape(why_text)}</div>
            </div>
            {risk_html}
        </div>
        """

    render_html(f'<div class="card-grid card-grid-1">{cards_html}</div>')

    if len(bullets) > max_items:
        with st.expander(f"Show {len(bullets) - max_items} more bullet rewrites"):
            for item in bullets[max_items:]:
                st.json(item)


def render_action_plan(result: dict):
    fixes = result.get("resume_fix_suggestions", [])
    learning = result.get("skill_gap_learning_plan", [])
    risks = result.get("eligibility_risks", [])

    st.markdown(
        '<div class="section-title">Recommended Next Actions</div>',
        unsafe_allow_html=True
    )

    actions = []

    for risk in risks[:2]:
        actions.append(
            {
                "title": clean_value(risk.get("risk_type", "Risk")),
                "action": clean_value(risk.get("recommendation", "")),
                "priority": clean_value(risk.get("severity", "Medium")),
                "source": "Risk"
            }
        )

    for fix in fixes[:3]:
        actions.append(
            {
                "title": clean_value(fix.get("issue", "Resume Fix")),
                "action": clean_value(fix.get("suggested_fix", "")),
                "priority": clean_value(fix.get("priority", "Medium")),
                "source": "Resume Fix"
            }
        )

    for item in learning[:2]:
        actions.append(
            {
                "title": clean_value(item.get("skill", "Skill Gap")),
                "action": clean_value(item.get("learning_action", "")),
                "priority": clean_value(item.get("priority", "Medium")),
                "source": "Learning Plan"
            }
        )

    if not actions:
        st.success("No immediate actions returned.")
        return

    cards_html = ""

    for idx, action in enumerate(actions[:5], start=1):
        chip_class = status_to_chip_class(action["priority"])
        priority_display = friendly_label(action["priority"])

        cards_html += f"""
        <div class="action-card">
            <div class="action-index">{idx}</div>
            <div class="action-content">
                <div class="modern-card-head">
                    <h4>{html.escape(action["title"] or "Review manually")}</h4>
                    <span class="chip {chip_class}">{html.escape(priority_display)}</span>
                </div>
                <p>{html.escape(action["action"] or "Review this item manually.")}</p>
                <span class="source-label">{html.escape(action["source"])}</span>
            </div>
        </div>
        """

    render_html(f'<div class="action-grid">{cards_html}</div>')
