import importlib
import pandas as pd
import streamlit as st

from source.loaders.resume_loader import extract_text_from_file
from source.loaders.jd_loader import extract_jd_text
from source.ai.llm_client import generate_resume_analysis
from source.ai.chat_client import generate_analysis_chat_response
from source.ai.providers import models_for_provider, provider_names
from source.services.report_generator import generate_pdf_report
from source.services.sample_analysis import sample_analysis_result
from source.services.job_tracker import (
    PRIORITY_OPTIONS,
    STATUS_OPTIONS,
    TRACKER_COLUMNS,
    load_job_tracker,
    new_job_from_analysis,
    normalize_tracker_df,
    save_job_tracker,
)
import source.ui.styles as styles
import source.ui.components as ui


# Force Streamlit to reload the latest saved source/ui/components.py.
# This prevents stale hot-reload/module-cache issues.
ui = importlib.reload(ui)
styles = importlib.reload(styles)
inject_global_styles = styles.inject_global_styles


APP_BUILD = "portfolio-ui-v3-2026-06-08"
SHOW_DEBUG = False


REQUIRED_UI_FUNCTIONS = [
    "render_navbar",
    "render_homepage",
    "render_page_header",
    "render_section_kicker",
    "render_verdict_card",
    "render_score_card",
    "render_recommendation_card",
    "render_score_radar",
    "render_top_strengths_concerns",
    "render_action_plan",
    "render_ats_donut",
    "render_requirement_status_bar",
    "render_missing_skill_priority_chart",
    "render_visual_note_card",
    "render_keyword_checklist",
    "render_summary_card",
    "render_card_grid",
    "render_chip_group",
    "render_risk_cards",
    "render_evidence_cards",
    "render_bullet_comparison",
    "normalize_analysis_result",
    "clean_value",
    "bullet_text",
]


missing_ui_functions = [
    function_name
    for function_name in REQUIRED_UI_FUNCTIONS
    if not hasattr(ui, function_name)
]

if missing_ui_functions:
    raise RuntimeError(
        "app.py is not loading the expected source/ui/components.py file.\n\n"
        f"Loaded file: {getattr(ui, '__file__', 'UNKNOWN')}\n"
        f"Missing functions: {missing_ui_functions}\n\n"
        "Open the loaded file path above, paste the latest full components.py there, save it, "
        "then restart Streamlit."
    )


def normalize_analysis_result(value):
    return ui.normalize_analysis_result(value)


st.set_page_config(
    page_title="TruthFit Resume AI",
    page_icon="TF",
    layout="wide"
)


if "page" not in st.session_state:
    st.session_state.page = "Home"

if "theme" not in st.session_state:
    st.session_state.theme = "Dark"

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""

if "jd_text" not in st.session_state:
    st.session_state.jd_text = ""

if "job_link" not in st.session_state:
    st.session_state.job_link = ""

if "include_cover_letter" not in st.session_state:
    st.session_state.include_cover_letter = False

if "provider" not in st.session_state:
    st.session_state.provider = "Gemini"

if "model" not in st.session_state:
    st.session_state.model = models_for_provider(st.session_state.provider)[0]

if "api_key" not in st.session_state:
    st.session_state.api_key = ""

if "user_projects" not in st.session_state:
    st.session_state.user_projects = ""

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

if "job_tracker_df" not in st.session_state:
    st.session_state.job_tracker_df = load_job_tracker()


inject_global_styles(st.session_state.theme)


def render_ai_settings():
    with st.sidebar:
        st.markdown("### AI Provider")

        provider = st.selectbox(
            "Provider",
            provider_names(),
            index=provider_names().index(st.session_state.provider),
            help="Use your own API key. Keys stay in this browser session and are not saved by the app.",
        )

        available_models = models_for_provider(provider)

        if provider != st.session_state.provider:
            st.session_state.provider = provider
            st.session_state.model = available_models[0]

        model_index = (
            available_models.index(st.session_state.model)
            if st.session_state.model in available_models
            else 0
        )

        st.session_state.model = st.selectbox(
            "Model",
            available_models,
            index=model_index,
        )

        st.session_state.api_key = st.text_input(
            f"{provider} API key",
            value=st.session_state.api_key,
            type="password",
            help="Required for live analysis and chat. Do not paste a subscription login; use an API key.",
        )

        st.caption("Use a temporary provider key for live testing and avoid uploading sensitive documents.")

        st.markdown('<div class="sidebar-demo-spacer"></div>', unsafe_allow_html=True)

        if st.button("Try Demo", type="primary", width="stretch", key="try_demo_sidebar"):
            st.session_state.page = "Demo"
            st.rerun()


def render_top_controls_with_theme_toggle():
    nav_col, spacer_col, theme_col = st.columns([4.8, 1.8, 0.8])

    with nav_col:
        nav_1, nav_2, nav_3, nav_4, nav_5 = st.columns(5, gap="small")

        nav_items = [
            (nav_1, "Home"),
            (nav_2, "Analyze"),
            (nav_3, "Dashboard"),
            (nav_4, "Chat"),
            (nav_5, "Tracker"),
        ]

        for column, page_name in nav_items:
            with column:
                if st.button(
                    page_name,
                    type="primary" if st.session_state.page == page_name else "secondary",
                    width="stretch",
                    key=f"nav_{page_name.lower()}"
                ):
                    st.session_state.page = page_name
                    st.rerun()

    with theme_col:
        current_dark = st.session_state.theme == "Dark"
        dark_mode = st.toggle(
            "Dark mode" if current_dark else "Light mode",
            value=current_dark,
            help="Toggle between light and dark theme",
            key="theme_toggle_switch"
        )

        if dark_mode != current_dark:
            st.session_state.theme = "Dark" if dark_mode else "Light"
            st.rerun()


render_ai_settings()
ui.render_navbar()
render_top_controls_with_theme_toggle()

if SHOW_DEBUG:
    st.caption(f"Build: {APP_BUILD}")
    st.caption(f"Loaded components.py: {getattr(ui, '__file__', 'UNKNOWN')}")


def show_analyze_page():
    ui.render_page_header(
        "Upload Resume and Job Description",
        "Upload your resume, upload or paste a job description, then generate a visual job-fit dashboard."
    )

    input_col, preview_col = st.columns([0.95, 1.05], gap="large")

    with input_col:
        ui.render_section_kicker("Resume Input")

        resume_file = st.file_uploader(
            "Upload Resume",
            type=["pdf", "docx", "txt"],
            help="Supported formats: PDF, DOCX, TXT"
        )

        ui.render_section_kicker("Job Description Input")

        jd_file = st.file_uploader(
            "Upload Job Description",
            type=["pdf", "docx", "txt"],
            help="Optional. You can upload a JD file or paste the JD below."
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
            placeholder="Paste the full job description here..."
        )

        st.session_state.include_cover_letter = st.toggle(
            "Generate cover letter",
            value=st.session_state.include_cover_letter,
            help="Optional. Generates a tailored cover letter based only on the resume and JD."
        )

        st.session_state.user_projects = st.text_area(
            "Projects or GitHub links",
            value=st.session_state.user_projects,
            height=160,
            placeholder=(
                "Optional: paste relevant projects, portfolio notes, or public GitHub links. "
                "The app will use this as user-provided evidence for project suggestions."
            ),
        )

        analyze_clicked = st.button(
            "Run TruthFit Analysis",
            type="primary",
            width="stretch"
        )

    with preview_col:
        ui.render_section_kicker("Live Input Preview")

        if resume_file is not None:
            try:
                resume_preview = extract_text_from_file(resume_file)
                st.session_state.resume_text = resume_preview

                st.markdown("#### Resume Preview")
                st.text_area(
                    "Extracted resume text",
                    value=resume_preview[:2500],
                    height=230,
                    disabled=True,
                    label_visibility="collapsed"
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
                    label_visibility="collapsed"
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

        with st.spinner("Generating visual TruthFit dashboard..."):
            result = generate_resume_analysis(
                resume_text=st.session_state.resume_text,
                job_description=st.session_state.jd_text,
                include_cover_letter=st.session_state.include_cover_letter,
                user_projects=st.session_state.user_projects,
                provider=st.session_state.provider,
                model=st.session_state.model,
                api_key=st.session_state.api_key,
            )

        normalized_result = normalize_analysis_result(result)
        normalized_result.setdefault("job_details", {})["job_link"] = st.session_state.job_link.strip()
        st.session_state.analysis_result = normalized_result
        st.session_state.chat_messages = []
        st.session_state.page = "Dashboard"
        st.rerun()


def show_dashboard_page(result_override=None, demo_mode: bool = False):
    result = result_override if result_override is not None else st.session_state.analysis_result

    if not result:
        st.warning("No analysis found. Go to the Analyze page first.")

        if st.button("Go to Analyze"):
            st.session_state.page = "Analyze"
            st.rerun()

        return

    result = normalize_analysis_result(result)
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
            else "A visual, evidence-based breakdown of how your resume fits this job."
        )
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

    st.write("")

    overview_left, overview_right = st.columns([1.05, 0.95], gap="large")

    with overview_left:
        ui.render_recommendation_card(summary)

    with overview_right:
        ui.render_score_radar(scores)

    ui.render_top_strengths_concerns(summary)

    st.write("")

    ui.render_action_plan(result)

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
            "Export"
        ]
    )

    with tab1:
        ui.render_page_header(
            "Visual Summary",
            "Quick visual explanation of resume-job alignment."
        )

        v1, v2 = st.columns(2, gap="large")

        with v1:
            ui.render_ats_donut(ats_keywords)

        with v2:
            ui.render_requirement_status_bar(jd_requirements)

        v3, v4 = st.columns([0.9, 1.1], gap="large")

        with v3:
            ui.render_missing_skill_priority_chart(skills.get("missing_skills", []))

        with v4:
            ui.render_visual_note_card()

        ui.render_keyword_checklist(ats_keywords)

    with tab2:
        ui.render_page_header(
            "Company and JD Details",
            "Parsed job context and risk signals from the job description."
        )

        j1, j2, j3 = st.columns(3, gap="medium")

        with j1:
            ui.render_summary_card(
                "Role",
                job.get("job_title", ""),
                job.get("company_name", "")
            )

        with j2:
            ui.render_summary_card(
                "Compensation / Work",
                job.get("salary_range", "Not specified"),
                f"Location: {job.get('location_or_work_policy', 'Not specified')}"
            )

        with j3:
            ui.render_summary_card(
                "Eligibility",
                job.get("sponsorship_policy", "Not specified"),
                f"Experience: {job.get('experience_required', 'Not specified')}"
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
            columns=2
        )

    with tab3:
        ui.render_page_header(
            "Skills and ATS Keyword Coverage",
            "Skill tags and keyword evidence extracted from the resume-JD comparison."
        )

        s1, s2, s3 = st.columns(3, gap="large")

        with s1:
            ui.render_chip_group(
                "Matched Skills",
                skills.get("matched_skills", []),
                key_name="skill"
            )

        with s2:
            ui.render_chip_group(
                "Missing Skills",
                skills.get("missing_skills", []),
                key_name="skill"
            )

        with s3:
            ui.render_chip_group(
                "Nice-to-have Skills",
                skills.get("nice_to_have_skills", []),
                key_name="skill"
            )

        ui.render_card_grid(
            title="ATS Keyword Evidence",
            items=ats_keywords,
            title_key="keyword",
            badge_key="coverage_status",
            body_keys=["importance", "resume_evidence"],
            empty_message="No ATS keyword evidence available.",
            columns=2
        )

        ui.render_card_grid(
            title="ATS Score Breakdown",
            items=ats_breakdown,
            title_key="category",
            badge_key="status",
            body_keys=["score", "evidence", "recommendation"],
            empty_message="No ATS score breakdown returned.",
            columns=2
        )

    with tab4:
        ui.render_page_header(
            "JD Requirement Analysis",
            "Must-have, nice-to-have, and job-title requirements translated into readable cards."
        )

        ui.render_requirement_status_bar(jd_requirements)

        ui.render_card_grid(
            title="Requirement Categories",
            items=jd_requirements.get("requirement_categories", []),
            title_key="category",
            badge_key="candidate_status",
            body_keys=["requirements"],
            empty_message="No requirement categories available.",
            columns=2
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
                columns=1
            )

        with r2:
            ui.render_card_grid(
                title="Nice-to-have Requirements",
                items=jd_requirements.get("nice_to_have", []),
                title_key="requirement",
                badge_key="status",
                body_keys=["priority", "recommendation", "resume_evidence"],
                empty_message="No nice-to-have requirements returned.",
                columns=1
            )

        ui.render_card_grid(
            title="Job Title Requirements",
            items=jd_requirements.get("job_title_requirements", []),
            title_key="requirement",
            badge_key="status",
            body_keys=["recommendation", "resume_evidence"],
            empty_message="No job-title requirements available.",
            columns=2
        )

    with tab5:
        ui.render_page_header(
            "Risks",
            "Eligibility, timeline, and hallucination-risk checks."
        )

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
                columns=1
            )

        with r2:
            ui.render_card_grid(
                title="Hallucination Guardrail",
                items=result.get("hallucination_guardrail", []),
                title_key="claim_or_skill",
                badge_key="status",
                body_keys=["evidence", "action"],
                empty_message="No hallucination risks detected.",
                columns=1
            )

    with tab6:
        ui.render_page_header(
            "Evidence-Based Matching",
            "Every match should be explainable from resume evidence."
        )

        ui.render_evidence_cards(
            result.get("evidence_based_matches", []),
            max_items=8
        )

    with tab7:
        ui.render_page_header(
            "Growth Plan",
            "Project and certification ideas tied to real JD gaps."
        )

        g1, g2 = st.columns(2, gap="large")

        with g1:
            ui.render_card_grid(
                title="Project Suggestions",
                items=result.get("project_suggestions", []),
                title_key="project_title",
                badge_key="priority",
                body_keys=["target_gap", "why_it_helps", "suggested_scope", "resume_bullet_example"],
                empty_message="No project suggestions returned.",
                columns=1
            )

        with g2:
            ui.render_card_grid(
                title="Certification Suggestions",
                items=result.get("certification_suggestions", []),
                title_key="certification",
                badge_key="priority",
                body_keys=["target_gap", "why_it_helps", "estimated_effort"],
                empty_message="No certification suggestions returned.",
                columns=1
            )

        ui.render_card_grid(
            title="Skill Gap Learning Plan",
            items=result.get("skill_gap_learning_plan", []),
            title_key="skill",
            badge_key="priority",
            body_keys=["why_needed", "learning_action", "mini_project_idea"],
            empty_message="No skill gap learning plan available.",
            columns=2
        )

    with tab8:
        ui.render_page_header(
            "Tailored Resume Preview",
            "Editable resume summary and bullet rewrites generated from supported evidence."
        )

        summary_text = tailored.get("tailored_summary", "")

        st.text_area(
            "Editable Tailored Summary",
            value=summary_text,
            height=170
        )

        rewritten_bullets = tailored.get("rewritten_bullets", [])
        rewritten_bullet_text = "\n".join(
            [f"- {bullet.get('rewritten', '')}" for bullet in rewritten_bullets]
        )

        st.text_area(
            "Editable Rewritten Bullets",
            value=rewritten_bullet_text,
            height=280
        )

        ui.render_bullet_comparison(
            result.get("before_after_bullets", []),
            max_items=6
        )

        ui.render_card_grid(
            title="Resume Fix Suggestions",
            items=result.get("resume_fix_suggestions", []),
            title_key="issue",
            badge_key="priority",
            body_keys=["why_it_matters", "suggested_fix"],
            empty_message="No resume fix suggestions available.",
            columns=2
        )

        if result.get("cover_letter"):
            ui.render_page_header(
                "Cover Letter",
                "Editable cover letter generated for this job description."
            )

            st.text_area(
                "Editable Cover Letter",
                value=result.get("cover_letter", ""),
                height=320
            )

    with tab9:
        ui.render_page_header(
            "Export",
            "Download a readable PDF report for this analysis."
        )

        report_pdf = generate_pdf_report(result)

        st.download_button(
            label="Download PDF Analysis Report",
            data=report_pdf,
            file_name="truthfit_resume_analysis_report.pdf",
            mime="application/pdf",
            width="stretch"
        )

        st.caption("The PDF uses readable sections and bullet points, not raw JSON.")


def show_demo_page():
    st.info(
        "This demo uses synthetic sample data and does not call Gemini, Claude, OpenAI, or Perplexity."
    )
    show_dashboard_page(result_override=sample_analysis_result(), demo_mode=True)


def add_current_analysis_to_tracker():
    if not st.session_state.analysis_result:
        st.warning("Run an analysis before adding a role to the tracker.")
        return

    current_df = normalize_tracker_df(st.session_state.job_tracker_df)
    new_row = new_job_from_analysis(st.session_state.analysis_result)

    match_mask = (
        (current_df["Company"].astype(str).str.lower() == str(new_row["Company"]).lower())
        & (current_df["Role"].astype(str).str.lower() == str(new_row["Role"]).lower())
    ) if not current_df.empty else pd.Series([], dtype=bool)

    if not current_df.empty and match_mask.any():
        current_df.loc[match_mask, TRACKER_COLUMNS] = pd.DataFrame([new_row]).iloc[0]
        st.session_state.job_tracker_df = current_df[TRACKER_COLUMNS]
        message = "Updated current role in the job tracker."
    else:
        st.session_state.job_tracker_df = pd.concat(
            [current_df, pd.DataFrame([new_row])],
            ignore_index=True,
        )[TRACKER_COLUMNS]
        message = "Added current analysis to the job tracker."

    save_job_tracker(st.session_state.job_tracker_df)
    st.success(message)


def show_tracker_page():
    ui.render_page_header(
        "Job Tracker",
        "Track applications, follow-ups, target salary, and match scores in one clean table."
    )

    st.session_state.job_tracker_df = normalize_tracker_df(st.session_state.job_tracker_df)

    if st.session_state.job_tracker_df.empty and st.session_state.analysis_result:
        st.session_state.job_tracker_df = pd.DataFrame(
            [new_job_from_analysis(st.session_state.analysis_result)]
        )[TRACKER_COLUMNS]
        save_job_tracker(st.session_state.job_tracker_df)

    metric_cols = st.columns(4, gap="medium")
    tracker_df = st.session_state.job_tracker_df

    status_counts = (
        tracker_df["Status"].value_counts().to_dict()
        if not tracker_df.empty and "Status" in tracker_df.columns
        else {}
    )

    with metric_cols[0]:
        ui.render_summary_card("Total Roles", str(len(tracker_df)), "Tracked opportunities")
    with metric_cols[1]:
        ui.render_summary_card("Applied", str(status_counts.get("Applied", 0)), "Submitted applications")
    with metric_cols[2]:
        ui.render_summary_card("Interview", str(status_counts.get("Interview", 0)), "Active conversations")
    with metric_cols[3]:
        ui.render_summary_card("Offers", str(status_counts.get("Offer", 0)), "Offer stage")

    left, right = st.columns([1, 1], gap="medium")

    with left:
        if st.button("Add Current Analysis", type="primary", width="stretch"):
            add_current_analysis_to_tracker()
            st.rerun()

    with right:
        if st.button("Reload Tracker", width="stretch"):
            st.session_state.job_tracker_df = load_job_tracker()
            st.rerun()

    edited_df = st.data_editor(
        st.session_state.job_tracker_df,
        num_rows="dynamic",
        width="stretch",
        column_config={
            "Status": st.column_config.SelectboxColumn("Status", options=STATUS_OPTIONS),
            "Priority": st.column_config.SelectboxColumn("Priority", options=PRIORITY_OPTIONS),
            "Job Link": st.column_config.LinkColumn("Job Link"),
            "Match Score": st.column_config.NumberColumn("Match Score", min_value=0, max_value=100),
        },
        hide_index=True,
        key="job_tracker_editor",
    )

    save_col, export_col = st.columns([1, 1], gap="medium")

    with save_col:
        if st.button("Save Tracker", type="primary", width="stretch"):
            st.session_state.job_tracker_df = normalize_tracker_df(edited_df)
            save_job_tracker(st.session_state.job_tracker_df)
            st.success("Tracker saved locally.")

    with export_col:
        st.download_button(
            "Export CSV",
            data=edited_df.to_csv(index=False).encode("utf-8"),
            file_name="truthfit_job_tracker.csv",
            mime="text/csv",
            width="stretch",
        )


def show_chat_page():
    ui.render_page_header(
        "Analysis Chat",
        "Ask follow-up questions, generate cover letters, and draft recruiter outreach from your current analysis."
    )

    if not st.session_state.analysis_result:
        st.warning("No analysis found. Go to Analyze first, then come back to chat.")

        if st.button("Go to Analyze", type="primary"):
            st.session_state.page = "Analyze"
            st.rerun()

        return

    quick_prompts = {
        "Explain Score": "Explain my score and the top three things I should fix first.",
        "Cover Letter": "Create a concise cover letter for this role based only on my evidence.",
        "Cold Email": "Write a short cold email to a recruiter or hiring manager for this role.",
        "Project Ideas": "Suggest the best portfolio projects I should build for this job.",
    }

    prompt_cols = st.columns(4, gap="small")

    for column, (label, prompt) in zip(prompt_cols, quick_prompts.items()):
        with column:
            if st.button(label, width="stretch"):
                st.session_state.pending_chat_prompt = prompt

    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_prompt = st.chat_input("Ask about this analysis, cover letter, cold email, or project plan...")

    if st.session_state.get("pending_chat_prompt"):
        user_prompt = st.session_state.pop("pending_chat_prompt")

    if not user_prompt:
        return

    st.session_state.chat_messages.append({"role": "user", "content": user_prompt})

    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking through your analysis..."):
            try:
                response = generate_analysis_chat_response(
                    question=user_prompt,
                    analysis_result=st.session_state.analysis_result,
                    resume_text=st.session_state.resume_text,
                    job_description=st.session_state.jd_text,
                    provider=st.session_state.provider,
                    model=st.session_state.model,
                    api_key=st.session_state.api_key,
                )
            except Exception as exc:
                response = f"Chat failed: {str(exc)}"

            st.markdown(response)

    st.session_state.chat_messages.append({"role": "assistant", "content": response})


if st.session_state.page == "Home":
    ui.render_homepage()

    st.write("")

    start_col1, start_col2, start_col3 = st.columns([1, 1, 1])

    with start_col2:
        if st.button(
            "Start Analysis",
            type="primary",
            width="stretch"
        ):
            st.session_state.page = "Analyze"
            st.rerun()

elif st.session_state.page == "Analyze":
    show_analyze_page()

elif st.session_state.page == "Dashboard":
    show_dashboard_page()

elif st.session_state.page == "Demo":
    show_demo_page()

elif st.session_state.page == "Chat":
    show_chat_page()

elif st.session_state.page == "Tracker":
    show_tracker_page()
