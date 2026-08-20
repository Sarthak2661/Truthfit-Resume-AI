import html

import streamlit as st

from source.ui.text_cleanup import (
    clean_value,
    display_field_value,
    friendly_field_label,
    friendly_label,
    get_score_class,
    get_score_label,
    get_score_meaning,
    render_html,
    severity_rank,
    status_to_chip_class,
    text_to_html,
)


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
                This review is automated and may be incomplete. Use it as a resume review aid,
                not as a hiring decision or guaranteed ATS result.
            </p>
        </div>
        """
    )


def render_privacy_notice():
    render_html(
        """
        <div class="tf-card privacy-card">
            <div class="mini-label">Privacy-First Mode</div>
            <h3>Personal details are removed before analysis.</h3>
            <p>
                TruthFit redacts detected names, phone numbers, emails, URLs, and street-style addresses
                before sending resume text to the selected AI provider. Uploaded resume and JD files are
                not saved by this app; only the current session text is used for analysis.
            </p>
            <p class="privacy-card-note">
                Provider note: live AI calls still go to the provider you choose, so avoid uploading
                sensitive documents unless you are comfortable with that provider's data policy.
            </p>
        </div>
        """
    )


def render_resume_evidence_score(evidence_summary: dict):
    if not evidence_summary:
        return

    score = int(evidence_summary.get("score", 0) or 0)
    supported = int(evidence_summary.get("supported", 0) or 0)
    partial = int(evidence_summary.get("partial", 0) or 0)
    missing = int(evidence_summary.get("missing", 0) or 0)
    unsafe = int(evidence_summary.get("unsafe", 0) or 0)
    top_gaps = evidence_summary.get("top_gaps", [])

    if score >= 80:
        score_label = "Strong proof"
        chip_class = "chip-green"
    elif score >= 60:
        score_label = "Needs clearer proof"
        chip_class = "chip-yellow"
    else:
        score_label = "Evidence is thin"
        chip_class = "chip-red"

    gap_rows = ""
    for item in top_gaps[:4]:
        if not isinstance(item, dict):
            continue

        gap_rows += f"""
        <tr>
            <td>{html.escape(clean_value(item.get("claim", "")))}</td>
            <td><span class="chip {status_to_chip_class(item.get("status", ""))}">{html.escape(clean_value(item.get("status", "")))}</span></td>
            <td>{html.escape(clean_value(item.get("evidence", "")) or "Not found in resume.")}</td>
            <td>{html.escape(clean_value(item.get("recommendation", "")) or "Verify before editing.")}</td>
        </tr>
        """

    table_html = (
        f"""
        <div class="evidence-proof-table-wrap">
            <table class="evidence-proof-table">
                <thead>
                    <tr>
                        <th>Claim</th>
                        <th>Status</th>
                        <th>Resume Evidence</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>{gap_rows}</tbody>
            </table>
        </div>
        """
        if gap_rows
        else "<p>No major unsupported resume claims were detected.</p>"
    )

    render_html(
        f"""
        <div class="tf-card evidence-proof-card">
            <div class="evidence-proof-top">
                <div>
                    <div class="mini-label">Resume Evidence Score</div>
                    <h3>{score}/100</h3>
                    <p>Measures whether claims are backed by concrete resume proof, not just ATS keyword matches.</p>
                </div>
                <span class="chip {chip_class}">{html.escape(score_label)}</span>
            </div>
            <div class="evidence-proof-metrics">
                <span><strong>{supported}</strong> Supported</span>
                <span><strong>{partial}</strong> Partial</span>
                <span><strong>{missing}</strong> Missing</span>
                <span><strong>{unsafe}</strong> Unsafe</span>
            </div>
            {table_html}
        </div>
        """
    )


def render_confidence_findings(findings: list, max_items: int = 5):
    st.markdown(
        '<div class="section-title">Proof Check</div>',
        unsafe_allow_html=True
    )

    if not findings:
        st.info("No proof checks available.")
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
                <span>Review Confidence</span>
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
        with st.expander(f"Show {len(findings) - max_items} more proof checks"):
            for item in findings[max_items:]:
                st.json(item)


def render_resume_heatmap(heatmap: dict):
    st.markdown(
        '<div class="section-title">Resume Proof Map</div>',
        unsafe_allow_html=True
    )

    if not heatmap or not heatmap.get("lines"):
        st.info("No resume heatmap data available yet.")
        return

    summary = heatmap.get("summary", {})
    metric_cols = st.columns(4, gap="small")

    metrics = [
        ("Highlighted Lines", summary.get("highlighted_lines", 0), "Resume lines with JD signal"),
        ("Covered Keywords", summary.get("covered_keywords", 0), "Directly supported terms"),
        ("Needs Proof", summary.get("partial_keywords", 0), "Partial keyword evidence"),
        ("Missing Keywords", summary.get("missing_keywords", 0), "Not found in resume"),
    ]

    for column, (title, value, subtitle) in zip(metric_cols, metrics):
        with column:
            render_summary_card(title, str(value), subtitle)

    legend_html = """
    <div class="heatmap-legend">
        <span><i class="heat-covered"></i>Strong resume/JD match</span>
        <span><i class="heat-partial"></i>Needs clearer proof</span>
        <span><i class="heat-neutral"></i>Neutral text</span>
    </div>
    """

    lines_html = ""

    for item in heatmap.get("lines", [])[:90]:
        text = clean_value(item.get("text", ""))
        status = clean_value(item.get("status", "neutral"))
        score = int(item.get("score", 0) or 0)
        keywords = item.get("matched_keywords", [])
        keyword_label = ", ".join([clean_value(keyword) for keyword in keywords if clean_value(keyword)])
        css_class = {
            "covered": "heat-line-covered",
            "partial": "heat-line-partial",
        }.get(status, "heat-line-neutral")

        keyword_html = (
            f'<span class="heat-keywords">{html.escape(keyword_label)}</span>'
            if keyword_label
            else ""
        )

        lines_html += f"""
        <div class="heatmap-line {css_class}" style="--heat:{max(0.06, score / 100):.2f}">
            <span class="heatmap-text">{html.escape(text)}</span>
            {keyword_html}
        </div>
        """

    missing = heatmap.get("missing_keywords", [])
    partial = heatmap.get("partial_keywords", [])
    recommendations = heatmap.get("recommendations", [])

    side_html = ""

    if missing:
        side_html += "<div class='heatmap-side-block'><h4>Missing Keywords</h4>"
        side_html += "".join(f"<span class='chip chip-red'>{html.escape(clean_value(item))}</span>" for item in missing[:12])
        side_html += "</div>"

    if partial:
        side_html += "<div class='heatmap-side-block'><h4>Needs More Proof</h4>"
        side_html += "".join(f"<span class='chip chip-yellow'>{html.escape(clean_value(item))}</span>" for item in partial[:12])
        side_html += "</div>"

    if recommendations:
        side_html += "<div class='heatmap-side-block'><h4>Analyzer Notes</h4><ul>"
        side_html += "".join(f"<li>{html.escape(clean_value(item))}</li>" for item in recommendations[:4])
        side_html += "</ul></div>"

    strongest_sections = summary.get("strongest_sections", [])
    if strongest_sections:
        side_html += "<div class='heatmap-side-block'><h4>Strongest Sections</h4>"
        side_html += "".join(f"<span class='chip chip-green'>{html.escape(clean_value(item))}</span>" for item in strongest_sections[:5])
        side_html += "</div>"

    render_html(
        f"""
        <div class="resume-heatmap-panel">
            {legend_html}
            <div class="resume-heatmap-grid">
                <div class="resume-heatmap-page" aria-label="Redacted resume heatmap">
                    {lines_html}
                </div>
                <div class="resume-heatmap-side">
                    {side_html}
                </div>
            </div>
        </div>
        """
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
    max_items: int = 5,
    adaptive: bool = True
):
    st.markdown(
        f'<div class="section-title">{html.escape(title)}</div>',
        unsafe_allow_html=True
    )

    if not items:
        st.info(empty_message)
        return

    body_keys = body_keys or []

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

    long_content_count = 0
    for item in sorted_items:
        if not isinstance(item, dict):
            long_content_count += 1 if len(clean_value(item)) > 220 else 0
            continue

        text_length = len(clean_value(item.get(title_key, "")))
        text_length += sum(len(clean_value(item.get(key, ""))) for key in body_keys)
        long_content_count += 1 if text_length > 420 or len(body_keys) >= 4 else 0

    if columns == 1 or (adaptive and long_content_count >= 2):
        grid_class = "card-grid card-grid-1"
    else:
        grid_class = "card-grid card-grid-adaptive"

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
        '<div class="section-title">Requirement Proof</div>',
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

