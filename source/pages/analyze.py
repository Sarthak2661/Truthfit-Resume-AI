import streamlit as st

from source.ai.llm_client import generate_resume_analysis
from source.loaders.jd_loader import extract_jd_text
from source.loaders.resume_loader import extract_text_from_file
from source.services.resume_heatmap import redact_personal_details
import source.ui.components as ui


def show_analyze_page():
    ui.render_page_header(
        "Upload Resume and Job Description",
        "Upload your resume, upload or paste a job description, then build a job-fit report.",
    )
    ui.render_privacy_notice()

    input_col, preview_col = st.columns([0.95, 1.05], gap="large")

    with input_col:
        ui.render_section_kicker("Resume Input")

        resume_file = st.file_uploader(
            "Upload Resume",
            type=["pdf", "docx", "txt"],
            help="Supported formats: PDF, DOCX, TXT",
        )

        ui.render_section_kicker("Job Description Input")

        jd_file = st.file_uploader(
            "Upload Job Description",
            type=["pdf", "docx", "txt"],
            help="Optional. You can upload a JD file or paste the JD below.",
        )

        st.session_state.job_link = st.text_input(
            "Job Posting Link",
            value=st.session_state.job_link,
            placeholder="https://company.com/careers/job-id",
            help="Optional. Add the original job post link so it appears in the dashboard and job tracker.",
        )

        pasted_jd = st.text_area(
            "Paste Job Description",
            height=220,
            placeholder="Paste the full job description here...",
        )

        st.session_state.include_cover_letter = st.toggle(
            "Generate cover letter",
            value=st.session_state.include_cover_letter,
            help="Optional. Generates a tailored cover letter based only on the resume and JD.",
        )

        st.session_state.user_projects = st.text_area(
            "Projects or GitHub links",
            value=st.session_state.user_projects,
            height=160,
            placeholder=(
                "Optional: paste relevant projects, portfolio notes, or public GitHub links. "
                "These details are treated as evidence for project suggestions."
            ),
        )

        analyze_clicked = st.button("Run TruthFit Analysis", type="primary", width="stretch")

    with preview_col:
        ui.render_section_kicker("Live Input Preview")

        if resume_file is not None:
            try:
                resume_preview = extract_text_from_file(resume_file)
                redacted_resume_preview = redact_personal_details(resume_preview)
                st.session_state.resume_text = redacted_resume_preview

                st.markdown("#### Resume Preview")
                st.caption("Personal details are redacted before preview, heatmap rendering, and live analysis.")
                st.text_area(
                    "Redacted extracted resume text",
                    value=redacted_resume_preview[:2500],
                    height=230,
                    disabled=True,
                    label_visibility="collapsed",
                )
            except Exception as exc:
                st.error(f"Could not read resume: {str(exc)}")

        try:
            jd_preview = extract_jd_text(jd_file, pasted_jd)
            st.session_state.jd_text = jd_preview

            if jd_preview:
                st.markdown("#### JD Preview")
                st.text_area(
                    "Extracted JD text",
                    value=jd_preview[:2500],
                    height=230,
                    disabled=True,
                    label_visibility="collapsed",
                )
        except Exception as exc:
            st.error(f"Could not read job description: {str(exc)}")

    if analyze_clicked:
        if resume_file is None:
            st.error("Please upload a resume.")
            return

        if not st.session_state.jd_text.strip():
            st.error("Please upload or paste a job description.")
            return

        with st.spinner("Building your TruthFit report..."):
            result = generate_resume_analysis(
                resume_text=st.session_state.resume_text,
                job_description=st.session_state.jd_text,
                include_cover_letter=st.session_state.include_cover_letter,
                user_projects=st.session_state.user_projects,
                provider=st.session_state.provider,
                model=st.session_state.model,
                api_key=st.session_state.api_key,
            )

        normalized_result = ui.normalize_analysis_result(result)
        normalized_result.setdefault("job_details", {})["job_link"] = st.session_state.job_link.strip()
        st.session_state.analysis_result = normalized_result
        st.session_state.chat_messages = []
        st.session_state.page = "Dashboard"
        st.rerun()
