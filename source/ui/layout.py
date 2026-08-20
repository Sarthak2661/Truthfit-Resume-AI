import html

import streamlit as st

from source.ui.text_cleanup import render_html


def render_page_header(title: str, subtitle: str = ""):
    render_html(
        f"""
        <div class="page-header">
            <h1>{html.escape(title)}</h1>
            <p>{html.escape(subtitle)}</p>
        </div>
        """
    )


def render_section_kicker(title: str):
    render_html(
        f"""
        <div class="section-kicker">
            {html.escape(title)}
        </div>
        """
    )


def render_navbar():
    if st.button("TruthFit Resume AI", key="brand_home_button", help="Go to homepage"):
        st.session_state.page = "Home"
        st.rerun()


# -------------------------------------------------
# Home page
# -------------------------------------------------


def render_feature_card(title: str, body: str):
    render_html(
        f"""
        <div class="tf-card feature-card">
            <h3>{html.escape(title)}</h3>
            <p>{html.escape(body)}</p>
        </div>
        """
    )


def render_homepage():
    render_html(
        """
        <div class="hero hero-split">
            <div class="hero-copy">
                <div class="mini-label">Resume checker and job-fit dashboard</div>
                <h1>See where your resume fits, <span class="gradient-text">and what to fix next.</span></h1>
                <p>
                    Upload a resume, paste a job description, and get a practical match review:
                    keyword coverage, skill gaps, eligibility notes, and rewrite ideas grounded in
                    experience already on the resume.
                </p>
                <div class="hero-metrics">
                    <div><strong>5</strong><span>fit scores</span></div>
                    <div><strong>ATS</strong><span>keyword map</span></div>
                    <div><strong>0</strong><span>unsupported claims</span></div>
                </div>
            </div>

            <div class="hero-visual" aria-label="Resume analysis preview">
                <div class="resume-sheet">
                    <div class="sheet-top"></div>
                    <div class="sheet-line wide"></div>
                    <div class="sheet-line"></div>
                    <div class="sheet-line short"></div>
                    <div class="sheet-section">
                        <span></span><span></span><span></span>
                    </div>
                    <div class="sheet-line wide"></div>
                    <div class="sheet-line"></div>
                    <div class="sheet-line short"></div>
                </div>

                <div class="ai-panel">
                    <div class="ai-ring">82</div>
                    <div>
                        <strong>Good Match</strong>
                        <span>Keyword and risk review</span>
                    </div>
                </div>

                <div class="keyword-strip">
                    <span>Covered</span>
                    <span>Needs proof</span>
                    <span>Missing</span>
                </div>
            </div>
        </div>
        """
    )

    st.write("")

    c1, c2, c3 = st.columns(3, gap="large")

    with c1:
        render_feature_card(
            "Upload",
            "Read PDF, DOCX, or TXT resumes and preview extracted content before analysis."
        )

    with c2:
        render_feature_card(
            "Compare",
            "Map resume evidence against job requirements, keywords, and eligibility signals."
        )

    with c3:
        render_feature_card(
            "Improve",
            "Get visual scores, careful rewrites, and a focused skill-gap learning plan."
        )

    st.write("")

    render_html(
        """
        <div class="process-band">
            <div>
                <span class="step-dot">1</span>
                <h3>Keyword Coverage</h3>
                <p>Shows covered, needs-proof, and missing terms without overwhelming tables.</p>
            </div>
            <div>
                <span class="step-dot">2</span>
                <h3>Evidence Check</h3>
                <p>Flags claims that need stronger support before they go on a resume.</p>
            </div>
            <div>
                <span class="step-dot">3</span>
                <h3>Action Plan</h3>
                <p>Turns gaps into specific resume fixes and learning steps.</p>
            </div>
        </div>
        """
    )


# -------------------------------------------------
# Dashboard cards
# -------------------------------------------------

