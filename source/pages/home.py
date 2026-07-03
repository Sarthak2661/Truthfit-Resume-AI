import streamlit as st

import source.ui.components as ui


def show_home_page():
    ui.render_homepage()

    st.write("")

    start_col1, start_col2, start_col3 = st.columns([1, 1, 1])

    with start_col2:
        if st.button("Start Analysis", type="primary", width="stretch"):
            st.session_state.page = "Analyze"
            st.rerun()
