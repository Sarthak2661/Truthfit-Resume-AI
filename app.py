import importlib

import streamlit as st

from source.ai.providers import models_for_provider, provider_names
from source.pages.analyze import show_analyze_page
from source.pages.chat import show_chat_page
from source.pages.dashboard import show_dashboard_page, show_demo_page
from source.pages.home import show_home_page
from source.pages.tracker import show_tracker_page
from source.services.job_tracker import load_job_tracker
from source.services.observability import configure_logging
import source.ui.components as ui
import source.ui.styles as styles


# Force Streamlit to reload the latest saved UI files during local development.
ui = importlib.reload(ui)
styles = importlib.reload(styles)
inject_global_styles = styles.inject_global_styles


APP_BUILD = "portfolio-polish-v4-2026-06-29"
SHOW_DEBUG = False


REQUIRED_UI_FUNCTIONS = [
    "render_navbar",
    "render_homepage",
    "render_page_header",
    "render_section_kicker",
    "render_verdict_card",
    "render_score_card",
    "render_recommendation_card",
    "render_privacy_notice",
    "render_resume_evidence_score",
    "render_score_radar",
    "render_score_driver_bar",
    "render_evidence_coverage_meter",
    "render_skill_match_table",
    "render_resume_heatmap",
    "render_top_strengths_concerns",
    "render_action_plan",
    "render_analysis_disclaimer",
    "render_confidence_findings",
    "render_fix_impact_matrix",
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


def verify_ui_contract():
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


def initialize_session_state():
    defaults = {
        "page": "Home",
        "theme": "Dark",
        "analysis_result": None,
        "resume_text": "",
        "jd_text": "",
        "job_link": "",
        "include_cover_letter": False,
        "provider": "Gemini",
        "api_key": "",
        "user_projects": "",
        "chat_messages": [],
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    if "model" not in st.session_state:
        st.session_state.model = models_for_provider(st.session_state.provider)[0]

    if "job_tracker_df" not in st.session_state:
        st.session_state.job_tracker_df = load_job_tracker()


def render_ai_settings():
    with st.sidebar:
        st.markdown("### Analysis Provider")

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

        st.session_state.model = st.selectbox("Model", available_models, index=model_index)

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
                    key=f"nav_{page_name.lower()}",
                ):
                    st.session_state.page = page_name
                    st.rerun()

    with theme_col:
        current_dark = st.session_state.theme == "Dark"
        dark_mode = st.toggle(
            "Dark mode" if current_dark else "Light mode",
            value=current_dark,
            help="Toggle between light and dark theme",
            key="theme_toggle_switch",
        )

        if dark_mode != current_dark:
            st.session_state.theme = "Dark" if dark_mode else "Light"
            st.rerun()


def render_current_page():
    routes = {
        "Home": show_home_page,
        "Analyze": show_analyze_page,
        "Dashboard": show_dashboard_page,
        "Demo": show_demo_page,
        "Chat": show_chat_page,
        "Tracker": show_tracker_page,
    }

    routes.get(st.session_state.page, show_home_page)()


st.set_page_config(page_title="TruthFit Resume AI", page_icon="TF", layout="wide")
configure_logging()
verify_ui_contract()
initialize_session_state()
inject_global_styles(st.session_state.theme)

render_ai_settings()
ui.render_navbar()
render_top_controls_with_theme_toggle()

if SHOW_DEBUG:
    st.caption(f"Build: {APP_BUILD}")
    st.caption(f"Loaded components.py: {getattr(ui, '__file__', 'UNKNOWN')}")

render_current_page()
