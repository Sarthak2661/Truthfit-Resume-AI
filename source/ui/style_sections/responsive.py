# ruff: noqa: F841,F541
def responsive_css(tokens: dict) -> str:
    is_dark = tokens["is_dark"]
    bg = tokens["bg"]
    card = tokens["card"]
    card_2 = tokens["card_2"]
    text = tokens["text"]
    muted = tokens["muted"]
    border = tokens["border"]
    primary = tokens["primary"]
    accent = tokens["accent"]
    warm = tokens["warm"]
    input_bg = tokens["input_bg"]
    input_text = tokens["input_text"]
    soft_panel = tokens["soft_panel"]
    nav_bg = tokens["nav_bg"]
    shadow = tokens["shadow"]
    primary_glow = tokens["primary_glow"]
    accent_glow = tokens["accent_glow"]
    warm_glow = tokens["warm_glow"]

    return f"""        @keyframes fadeInUp {{
            from {{
                opacity:0;
                transform:translateY(14px);
            }}
            to {{
                opacity:1;
                transform:translateY(0);
            }}
        }}

        @media screen and (max-width:900px) {{
            .hero-split,
            .verdict-card,
            .card-grid,
            .keyword-grid,
            .resume-heatmap-grid,
            .action-grid,
            .compare-grid {{
                grid-template-columns:1fr;
            }}

            .heatmap-line {{
                flex-direction:column;
                gap:6px;
            }}

            .heat-keywords {{
                max-width:100%;
                white-space:normal;
            }}

            .hero h1 {{
                font-size:42px;
            }}

            .hero {{
                padding:38px 24px;
            }}

            .hero-metrics,
            .process-band {{
                grid-template-columns:1fr;
            }}

            .evidence-proof-top {{
                flex-direction:column;
            }}

            .evidence-proof-metrics {{
                grid-template-columns:repeat(2, minmax(0, 1fr));
            }}

            .hero-visual {{
                min-height:320px;
            }}

            .truthfit-navbar {{
                flex-direction:column;
                align-items:flex-start;
                gap:10px;
            }}

            .keyword-badges {{
                align-items:flex-start;
            }}

            .keyword-card-top,
            .modern-card-head {{
                flex-direction:column;
            }}

            .page-header h1 {{
                font-size:30px;
            }}

            .section-title {{
                font-size:25px;
            }}
        }}
    """
