import html

import pandas as pd
import streamlit as st

from source.ui.text_cleanup import clean_value, friendly_label, render_html, status_to_chip_class


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
            <div class="section-title no-top-margin">Keyword Details</div>
            <div class="keyword-grid">
                {rows_html}
            </div>
        </div>
        """
    )


# -------------------------------------------------
# Risk / evidence / rewrite / action cards
# -------------------------------------------------

