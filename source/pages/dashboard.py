import streamlit as st

from source.services.report_generator import generate_pdf_report
from source.services.sample_analysis import sample_analysis_result
import source.ui.components as ui


def show_dashboard_page(result_override=None, demo_mode: bool = False):
    result = result_override if result_override is not None else st.session_state.analysis_result

    if not result:
        st.warning("No analysis found. Go to the Analyze page first.")

        if st.button("Go to Analyze"):
            st.session_state.page = "Analyze"
            st.rerun()

        return

    result = ui.normalize_analysis_result(result)
    if not demo_mode:
        st.session_state.analysis_result = result

    job = result.get("job_details", {})
    scores = result.get("scores", {})
    summary = result.get("match_summary", {})
    jd_requirements = result.get("jd_requirements", {})
    skills = result.get("skills_analysis", {})
    tailored = result.get("tailored_resume_content", {})
    ats_keywords = result.get("ats_keyword_coverage", [])
    ats_breakdown = result.get("ats_score_breakdown", [])

    ui.render_page_header(
        "Demo Dashboard" if demo_mode else "Dashboard",
        (
            "A no-API sample dashboard using synthetic resume and job data."
            if demo_mode
            else "A visual breakdown of how your resume fits this job."
        ),
    )

    score_cols = st.columns(5, gap="medium")
    score_items = [
        ("Overall Match", scores.get("overall_match_score", 0)),
        ("Technical Match", scores.get("technical_match_score", 0)),
        ("ATS Coverage", scores.get("ats_keyword_coverage_score", 0)),
        ("Eligibility", scores.get("eligibility_score", 0)),
        ("Experience", scores.get("experience_match_score", 0)),
    ]

    for column, (label, value) in zip(score_cols, score_items):
        with column:
            ui.render_score_card(label, int(value or 0))

    st.write("")
    ui.render_verdict_card(result)
    ui.render_analysis_disclaimer()
    st.write("")

    ui.render_recommendation_card(summary)
    ui.render_top_strengths_concerns(summary)
    st.write("")

    ui.render_fix_impact_matrix(result.get("fix_impact_matrix", []))
    st.write("")
    ui.render_confidence_findings(result.get("confidence_findings", []))

    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs(
        [
            "Visual Summary",
            "Job Details",
            "Skills & ATS",
            "Requirements",
            "Risks",
            "Evidence",
            "Growth Plan",
            "Resume Rewrite",
            "Export",
        ]
    )

    with tab1:
        ui.render_page_header("Visual Summary", "Quick visual explanation of resume-job alignment.")

        ui.render_score_driver_bar(result)

        st.write("")
        ui.render_evidence_coverage_meter(result)

        st.write("")
        v1, v2 = st.columns(2, gap="large")

        with v1:
            ui.render_ats_donut(ats_keywords)

        with v2:
            ui.render_missing_skill_priority_chart(skills.get("missing_skills", []))

        ui.render_keyword_checklist(ats_keywords)

    with tab2:
        ui.render_page_header(
            "Company and JD Details",
            "Parsed job context and risk signals from the job description.",
        )

        j1, j2, j3 = st.columns(3, gap="medium")

        with j1:
            ui.render_summary_card("Role", job.get("job_title", ""), job.get("company_name", ""))

        with j2:
            ui.render_summary_card(
                "Compensation / Work",
                job.get("salary_range", "Not specified"),
                f"Location: {job.get('location_or_work_policy', 'Not specified')}",
            )

        with j3:
            ui.render_summary_card(
                "Eligibility",
                job.get("sponsorship_policy", "Not specified"),
                f"Experience: {job.get('experience_required', 'Not specified')}",
            )

        job_link = str(job.get("job_link", "") or "").strip()
        if job_link:
            st.markdown(f"**Job posting:** [Open original posting]({job_link})")

        ui.render_card_grid(
            title="JD Red Flags",
            items=result.get("jd_red_flags", []),
            title_key="flag",
            badge_key="severity",
            body_keys=["why_it_matters", "candidate_impact"],
            empty_message="No JD red flags found.",
            columns=2,
        )

    with tab3:
        ui.render_page_header(
            "Skills and ATS Keyword Coverage",
            "Skill tags and keyword evidence extracted from the resume-JD comparison.",
        )

        ui.render_skill_match_table(skills, ats_keywords)

        ui.render_card_grid(
            title="ATS Score Breakdown",
            items=ats_breakdown,
            title_key="category",
            badge_key="status",
            body_keys=["score", "evidence", "recommendation"],
            empty_message="No ATS score breakdown returned.",
            columns=2,
        )

    with tab4:
        ui.render_page_header(
            "JD Requirement Analysis",
            "Must-have, nice-to-have, and job-title requirements translated into readable cards.",
        )

        ui.render_card_grid(
            title="Requirement Categories",
            items=jd_requirements.get("requirement_categories", []),
            title_key="category",
            badge_key="candidate_status",
            body_keys=["requirements"],
            empty_message="No requirement categories available.",
            columns=2,
        )

        r1, r2 = st.columns(2, gap="large")

        with r1:
            ui.render_card_grid(
                title="Must-have Requirements",
                items=jd_requirements.get("must_have", []),
                title_key="requirement",
                badge_key="status",
                body_keys=["priority", "recommendation", "resume_evidence"],
                empty_message="No must-have requirements returned.",
                columns=1,
            )

        with r2:
            ui.render_card_grid(
                title="Nice-to-have Requirements",
                items=jd_requirements.get("nice_to_have", []),
                title_key="requirement",
                badge_key="status",
                body_keys=["priority", "recommendation", "resume_evidence"],
                empty_message="No nice-to-have requirements returned.",
                columns=1,
            )

        ui.render_card_grid(
            title="Job Title Requirements",
            items=jd_requirements.get("job_title_requirements", []),
            title_key="requirement",
            badge_key="status",
            body_keys=["recommendation", "resume_evidence"],
            empty_message="No job-title requirements available.",
            columns=2,
        )

    with tab5:
        ui.render_page_header("Risks", "Eligibility, timeline, and unsupported-claim checks.")
        ui.render_risk_cards(result.get("eligibility_risks", []))

        r1, r2 = st.columns(2, gap="large")

        with r1:
            ui.render_card_grid(
                title="Resume Timeline Checker",
                items=result.get("resume_timeline_check", []),
                title_key="issue",
                badge_key="severity",
                body_keys=["evidence", "recommendation"],
                empty_message="No timeline issues detected.",
                columns=1,
            )

        with r2:
            ui.render_card_grid(
                title="Unsupported Claims Check",
                items=result.get("hallucination_guardrail", []),
                title_key="claim_or_skill",
                badge_key="status",
                body_keys=["evidence", "action"],
                empty_message="No unsupported claims detected.",
                columns=1,
            )

    with tab6:
        ui.render_page_header(
            "Evidence-Based Matching",
            "Every match should be explainable from resume evidence.",
        )
        ui.render_evidence_cards(result.get("evidence_based_matches", []), max_items=8)

    with tab7:
        ui.render_page_header("Growth Plan", "Project and certification ideas tied to real JD gaps.")

        g1, g2 = st.columns(2, gap="large")

        with g1:
            ui.render_card_grid(
                title="Project Suggestions",
                items=result.get("project_suggestions", []),
                title_key="project_title",
                badge_key="priority",
                body_keys=["target_gap", "why_it_helps", "suggested_scope", "resume_bullet_example"],
                empty_message="No project suggestions returned.",
                columns=1,
            )

        with g2:
            ui.render_card_grid(
                title="Certification Suggestions",
                items=result.get("certification_suggestions", []),
                title_key="certification",
                badge_key="priority",
                body_keys=["target_gap", "why_it_helps", "estimated_effort"],
                empty_message="No certification suggestions returned.",
                columns=1,
            )

        ui.render_card_grid(
            title="Skill Gap Learning Plan",
            items=result.get("skill_gap_learning_plan", []),
            title_key="skill",
            badge_key="priority",
            body_keys=["why_needed", "learning_action", "mini_project_idea"],
            empty_message="No skill gap learning plan available.",
            columns=2,
        )

    with tab8:
        ui.render_page_header(
            "Tailored Resume Preview",
            "Editable resume summary and bullet rewrites generated from supported evidence.",
        )

        st.text_area("Editable Tailored Summary", value=tailored.get("tailored_summary", ""), height=170)

        rewritten_bullets = tailored.get("rewritten_bullets", [])
        rewritten_bullet_text = "\n".join([f"- {bullet.get('rewritten', '')}" for bullet in rewritten_bullets])

        st.text_area("Editable Rewritten Bullets", value=rewritten_bullet_text, height=280)
        ui.render_bullet_comparison(result.get("before_after_bullets", []), max_items=6)

        ui.render_card_grid(
            title="Resume Fix Suggestions",
            items=result.get("resume_fix_suggestions", []),
            title_key="issue",
            badge_key="priority",
            body_keys=["why_it_matters", "suggested_fix"],
            empty_message="No resume fix suggestions available.",
            columns=2,
        )

        if result.get("cover_letter"):
            ui.render_page_header("Cover Letter", "Editable cover letter generated for this job description.")
            st.text_area("Editable Cover Letter", value=result.get("cover_letter", ""), height=320)

    with tab9:
        ui.render_page_header("Export", "Download a readable PDF report for this analysis.")
        report_pdf = generate_pdf_report(result)

        st.download_button(
            label="Download PDF Analysis Report",
            data=report_pdf,
            file_name="truthfit_resume_analysis_report.pdf",
            mime="application/pdf",
            width="stretch",
        )

        st.caption("The PDF uses readable sections and bullet points, not raw JSON.")


def show_demo_page():
    st.info("This demo uses synthetic sample data and does not call Gemini, Claude, OpenAI, or Perplexity.")
    show_dashboard_page(result_override=sample_analysis_result(), demo_mode=True)
