import streamlit as st

from source.ui.style_sections import (
    base_css,
    component_css,
    dashboard_css,
    home_css,
    navigation_css,
    responsive_css,
)
from source.ui.style_tokens import theme_tokens


def inject_global_styles(theme: str):
    tokens = theme_tokens(theme)
    css = "\n".join(
        [
            base_css(tokens),
            navigation_css(tokens),
            home_css(tokens),
            component_css(tokens),
            dashboard_css(tokens),
            responsive_css(tokens),
        ]
    )

    st.markdown(
        f"""
        <style>
        {css}
        </style>
        """,
        unsafe_allow_html=True,
    )
