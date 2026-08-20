from collections import Counter

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from source.ui.cards import render_summary_card
from source.ui.text_cleanup import clean_value, friendly_label, is_dark_theme, unique_chart_key


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

    apply_chart_layout(fig, 340, "Keyword Coverage")

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

