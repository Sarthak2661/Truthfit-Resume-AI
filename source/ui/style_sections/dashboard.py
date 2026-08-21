# ruff: noqa: F841,F541
def dashboard_css(tokens: dict) -> str:
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

    return f"""        .stTabs [data-baseweb="tab-list"] {{
            gap:8px;
            border-bottom:1px solid {border};
            padding-bottom:8px;
            flex-wrap:wrap;
        }}

        .stTabs [data-baseweb="tab"] {{
            border-radius:12px;
            padding:10px 18px;
            background:{nav_bg};
            border:1px solid {border};
            font-size:15px;
            font-weight:800;
            color:{text};
        }}

        .stTabs [data-baseweb="tab"][aria-selected="true"] {{
            background:linear-gradient(135deg, {primary}, {accent});
            border-color:transparent;
            color:#FFFFFF;
        }}

        .stTabs [data-baseweb="tab"][aria-selected="true"] p {{
            color:#FFFFFF !important;
        }}

        .stTabs [data-baseweb="tab-highlight"] {{
            display:none;
        }}

        .resume-heatmap-panel {{
            margin-top:18px;
        }}

        [data-testid="stExpander"] .resume-heatmap-panel {{
            margin-top:10px;
        }}

        .heatmap-legend {{
            display:flex;
            flex-wrap:wrap;
            gap:10px;
            margin:8px 0 18px;
        }}

        .heatmap-legend span {{
            display:inline-flex;
            align-items:center;
            gap:8px;
            padding:8px 12px;
            border:1px solid {border};
            border-radius:999px;
            color:{muted};
            background:{card};
            font-size:13px;
            font-weight:800;
        }}

        .heatmap-legend i {{
            width:14px;
            height:14px;
            border-radius:999px;
            display:inline-block;
        }}

        .heat-covered {{
            background:rgba(34,197,94,0.72);
        }}

        .heat-partial {{
            background:rgba(245,158,11,0.72);
        }}

        .heat-neutral {{
            background:rgba(148,163,184,0.28);
        }}

        .resume-heatmap-grid {{
            display:grid;
            grid-template-columns:minmax(0, 1.7fr) minmax(280px, 0.8fr);
            gap:18px;
            align-items:start;
        }}

        .resume-heatmap-page,
        .resume-heatmap-side {{
            background:{card};
            border:1px solid {border};
            border-radius:20px;
            box-shadow:{shadow};
        }}

        .resume-heatmap-page {{
            padding:18px;
            max-height:760px;
            overflow:auto;
        }}

        .resume-heatmap-side {{
            padding:18px;
            display:grid;
            gap:14px;
        }}

        .heatmap-line {{
            position:relative;
            display:flex;
            justify-content:space-between;
            gap:14px;
            padding:8px 10px;
            margin:3px 0;
            border-radius:10px;
            border:1px solid transparent;
            line-height:1.55;
            overflow:hidden;
        }}

        .heatmap-line::before {{
            content:"";
            position:absolute;
            inset:0;
            opacity:calc(0.12 + var(--heat) * 0.38);
            pointer-events:none;
        }}

        .heat-line-covered {{
            border-color:rgba(34,197,94,0.20);
        }}

        .heat-line-covered::before {{
            background:linear-gradient(90deg, rgba(34,197,94,0.68), rgba(34,197,94,0.08));
        }}

        .heat-line-partial {{
            border-color:rgba(245,158,11,0.24);
        }}

        .heat-line-partial::before {{
            background:linear-gradient(90deg, rgba(245,158,11,0.72), rgba(245,158,11,0.08));
        }}

        .heat-line-neutral {{
            background:rgba(148,163,184,0.05);
        }}

        .heatmap-text,
        .heat-keywords {{
            position:relative;
            z-index:1;
        }}

        .heatmap-text {{
            color:{text};
            min-width:0;
        }}

        .heat-keywords {{
            flex:0 0 auto;
            align-self:flex-start;
            max-width:220px;
            padding:5px 8px;
            border-radius:999px;
            background:{card_2};
            color:{muted};
            font-size:12px;
            font-weight:900;
            overflow:hidden;
            text-overflow:ellipsis;
            white-space:nowrap;
        }}

        .heatmap-side-block {{
            border:1px solid {border};
            border-radius:16px;
            padding:14px;
            background:{card_2};
        }}

        .heatmap-side-block h4 {{
            margin:0 0 10px;
            font-size:15px;
        }}

        .heatmap-side-block ul {{
            margin:0;
            padding-left:18px;
        }}

        .heatmap-side-block li {{
            color:{muted};
            margin-bottom:8px;
            line-height:1.55;
        }}
    """
