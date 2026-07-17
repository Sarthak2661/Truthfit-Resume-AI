import streamlit as st

from source.services.report_generator import generate_pdf_report
from source.services.evidence_score import add_resume_evidence_score
from source.services.resume_heatmap import build_resume_heatmap
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

    result = add_resume_evidence_score(ui.normalize_analysis_result(result))
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
    resume_heatmap_text = result.get("resume_heatmap_text") or st.session_state.get("resume_text", "")
    resume_heatmap = build_resume_heatmap(resume_heatmap_text, result)

    ui.render_page_header(
        "Sample Report" if demo_mode else "Dashboard",
        (
            "A no-API preview using sample resume and job data."
            if demo_mode
            else "A practical breakdown of how your resume fits this job."
        ),
    )

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "Privacy & Overview",
            "Skills & Requirements",
            "Evidence & Risks",
            "Improve Resume",
            "Export & Track",
        ]
    )

    with tab1:
        ui.render_page_header(
            "Privacy-First Overview",
            "Start with the verdict, proof quality, score drivers, and the highest-impact fixes.",
        )

        ui.render_privacy_notice()

        score_cols = st.columns(6, gap="medium")
        score_items = [
            ("Overall Match", scores.get("overall_match_score", 0)),
            ("Technical Match", scores.get("technical_match_score", 0)),
            ("ATS Coverage", scores.get("ats_keyword_coverage_score", 0)),
            ("Evidence Proof", scores.get("resume_evidence_score", 0)),
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

        ui.render_score_driver_bar(result)
        st.write("")

        ui.render_resume_evidence_score(result.get("resume_evidence_summary", {}))
        st.write("")

        ui.render_recommendation_card(summary)
        ui.render_top_strengths_concerns(summary)
        st.write("")

        ui.render_fix_impact_matrix(result.get("fix_impact_matrix", [])[:3])

    with tab2:
        ui.render_page_header("Skills & Requirements", "Role details, skill evidence, and JD requirements.")

        job_cols = st.columns(3, gap="medium")
        with job_cols[0]:
            ui.render_summary_card("Role", job.get("job_title", ""), job.get("company_name", ""))
        with job_cols[1]:
            ui.render_summary_card(
                "Compensation / Work",
                job.get("salary_range", "Not specified"),
                f"Location: {job.get('location_or_work_policy', 'Not specified')}",
            )
        with job_cols[2]:
            ui.render_summary_card(
                "Eligibility",
                job.get("sponsorship_policy", "Not specified"),
                f"Experience: {job.get('experience_required', 'Not specified')}",
            )

        job_link = str(job.get("job_link", "") or "").strip()
        if job_link:
            st.markdown(f"**Job posting:** [Open original posting]({job_link})")

        ui.render_skill_match_table(skills, ats_keywords)

        ui.render_card_grid(
            title="Must-have Requirements",
            items=jd_requirements.get("must_have", []),
            title_key="requirement",
            badge_key="status",
            body_keys=["priority", "recommendation", "resume_evidence"],
            empty_message="No must-have requirements returned.",
            columns=1,
        )

        ui.render_card_grid(
            title="Nice-to-have Requirements",
            items=jd_requirements.get("nice_to_have", []),
            title_key="requirement",
            badge_key="status",
            body_keys=["priority", "recommendation", "resume_evidence"],
            empty_message="No nice-to-have requirements returned.",
            columns=1,
        )

        with st.expander("Show ATS score details"):
            ui.render_card_grid(
                title="ATS Score Breakdown",
                items=ats_breakdown,
                title_key="category",
                badge_key="status",
                body_keys=["score", "evidence", "recommendation"],
                empty_message="No ATS score breakdown returned.",
                columns=2,
            )

            ui.render_keyword_checklist(ats_keywords)

        with st.expander("Show requirement categories and title checks"):
            ui.render_card_grid(
                title="Requirement Categories",
                items=jd_requirements.get("requirement_categories", []),
                title_key="category",
                badge_key="candidate_status",
                body_keys=["requirements"],
                empty_message="No requirement categories available.",
                columns=2,
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

    with tab3:
        ui.render_page_header(
            "Evidence & Risks",
            "Proof checks, unsupported claims, eligibility risks, and optional resume proof map.",
        )

        ui.render_confidence_findings(result.get("confidence_findings", []), max_items=3)

        ui.render_card_grid(
            title="Unsupported Claims Check",
            items=result.get("hallucination_guardrail", []),
            title_key="claim_or_skill",
            badge_key="status",
            body_keys=["evidence", "action"],
            empty_message="No unsupported claims detected.",
            columns=1,
        )

        ui.render_risk_cards(result.get("eligibility_risks", []))

        with st.expander("Show requirement proof details"):
            ui.render_evidence_cards(result.get("evidence_based_matches", []), max_items=8)

        with st.expander("Show evidence coverage counts"):
            ui.render_evidence_coverage_meter(result)

        with st.expander("Show timeline checks"):
            ui.render_card_grid(
                title="Resume Timeline Checker",
                items=result.get("resume_timeline_check", []),
                title_key="issue",
                badge_key="severity",
                body_keys=["evidence", "recommendation"],
                empty_message="No timeline issues detected.",
                columns=1,
            )

        with st.expander("Show JD red flags"):
            ui.render_card_grid(
                title="JD Red Flags",
                items=result.get("jd_red_flags", []),
                title_key="flag",
                badge_key="severity",
                body_keys=["why_it_matters", "candidate_impact"],
                empty_message="No JD red flags found.",
                columns=2,
            )

        with st.expander("Open Resume Proof Map"):
            st.caption(
                "This is not eye-tracking data. It highlights redacted resume lines based on job keyword "
                "alignment and evidence strength."
            )
            ui.render_resume_heatmap(resume_heatmap)

    with tab4:
        ui.render_page_header("Improve Resume", "Rewrites, fixes, projects, and certifications tied to role gaps.")

        st.text_area("Editable Tailored Summary", value=tailored.get("tailored_summary", ""), height=170)

        rewritten_bullets = tailored.get("rewritten_bullets", [])
        rewritten_bullet_text = "\n".join([f"- {bullet.get('rewritten', '')}" for bullet in rewritten_bullets])

        st.text_area("Editable Rewritten Bullets", value=rewritten_bullet_text, height=240)
        ui.render_bullet_comparison(result.get("before_after_bullets", []), max_items=5)

        ui.render_card_grid(
            title="Resume Fix Suggestions",
            items=result.get("resume_fix_suggestions", []),
            title_key="issue",
            badge_key="priority",
            body_keys=["why_it_matters", "suggested_fix"],
            empty_message="No resume fix suggestions available.",
            columns=2,
        )

        ui.render_card_grid(
            title="Project Suggestions",
            items=result.get("project_suggestions", []),
            title_key="project_title",
            badge_key="priority",
            body_keys=["target_gap", "why_it_helps", "suggested_scope", "resume_bullet_example"],
            empty_message="No project suggestions returned.",
            columns=1,
        )

        ui.render_card_grid(
            title="Certification Suggestions",
            items=result.get("certification_suggestions", []),
            title_key="certification",
            badge_key="priority",
            body_keys=["target_gap", "why_it_helps", "estimated_effort"],
            empty_message="No certification suggestions returned.",
            columns=1,
        )

        with st.expander("Show skill gap learning plan"):
            ui.render_card_grid(
                title="Skill Gap Learning Plan",
                items=result.get("skill_gap_learning_plan", []),
                title_key="skill",
                badge_key="priority",
                body_keys=["why_needed", "learning_action", "mini_project_idea"],
                empty_message="No skill gap learning plan available.",
                columns=2,
            )

        if result.get("cover_letter"):
            ui.render_page_header("Cover Letter", "Editable cover letter generated for this job description.")
            st.text_area("Editable Cover Letter", value=result.get("cover_letter", ""), height=320)

    with tab5:
        ui.render_page_header("Export & Track", "Download the report, save this role, or continue in the tracker.")

        export_cols = st.columns(3, gap="medium")
        with export_cols[0]:
            ui.render_summary_card("Role", job.get("job_title", "Not specified"), job.get("company_name", ""))
        with export_cols[1]:
            ui.render_summary_card("Match Score", f"{scores.get('overall_match_score', 0)}/100", summary.get("apply_recommendation", ""))
        with export_cols[2]:
            ui.render_summary_card("Tracker", "Ready", "Save this analysis as an opportunity")

        if job_link:
            st.markdown(f"**Job posting:** [Open original posting]({job_link})")

        action_col1, action_col2 = st.columns(2, gap="medium")

        report_pdf = generate_pdf_report(result)

        with action_col1:
            st.download_button(
                label="Download PDF Analysis Report",
                data=report_pdf,
                file_name="truthfit_resume_analysis_report.pdf",
                mime="application/pdf",
                width="stretch",
            )

        with action_col2:
            if st.button("Open Job Tracker", type="primary", width="stretch"):
                st.session_state.page = "Tracker"
                st.rerun()

        st.caption("The PDF uses readable sections and bullet points, not raw JSON.")


def show_demo_page():
    st.info("This preview uses sample data and does not call Gemini, Claude, OpenAI, or Perplexity.")
    show_dashboard_page(result_override=sample_analysis_result(), demo_mode=True)
