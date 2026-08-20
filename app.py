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


inject_global_styles = styles.inject_global_styles


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
initialize_session_state()
inject_global_styles(st.session_state.theme)

render_ai_settings()
ui.render_navbar()
render_top_controls_with_theme_toggle()

render_current_page()
