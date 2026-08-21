# ruff: noqa: F841,F541
def navigation_css(tokens: dict) -> str:
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

    return f"""        .truthfit-navbar {{
            display:flex;
            align-items:center;
            justify-content:space-between;
            padding:16px 18px;
            border:1px solid {border};
            border-radius:18px;
            background:{soft_panel};
            backdrop-filter:blur(18px);
            margin-bottom:18px;
            box-shadow:{shadow};
        }}

        .st-key-brand_home_button {{
            padding:20px 26px;
            border:1px solid {border};
            border-radius:24px;
            background:{soft_panel};
            backdrop-filter:blur(18px);
            margin-bottom:18px;
            box-shadow:{shadow};
        }}

        .st-key-brand_home_button button {{
            background:transparent !important;
            border:0 !important;
            box-shadow:none !important;
            min-height:auto !important;
            padding:0 !important;
            color:{text} !important;
            font-size:clamp(30px, 4vw, 52px) !important;
            font-weight:900 !important;
            letter-spacing:0 !important;
            line-height:1.2 !important;
            text-align:left !important;
            justify-content:flex-start !important;
            width:100% !important;
        }}

        .st-key-brand_home_button button p {{
            font-size:clamp(30px, 4vw, 52px) !important;
            line-height:1.05 !important;
            margin:0 !important;
            background:linear-gradient(90deg, {text} 0%, {primary} 58%, {accent} 100%);
            -webkit-background-clip:text;
            -webkit-text-fill-color:transparent;
        }}

        .st-key-brand_home_button button:hover {{
            color:{primary} !important;
            border:0 !important;
            background:transparent !important;
            transform:none !important;
        }}

        .truthfit-brand {{
            font-size:22px;
            font-weight:900;
            letter-spacing:0;
            color:{text};
        }}

        .truthfit-brand span {{
            color:{primary};
        }}

        .page-header {{
            margin-top:18px;
            margin-bottom:22px;
        }}

        .page-header h1 {{
            font-size:34px;
            line-height:1.15;
            margin:0 0 8px;
            letter-spacing:0;
        }}

        .page-header p {{
            color:{muted};
            font-size:16px;
            line-height:1.6;
            margin:0;
        }}

        .section-title {{
            font-size:28px;
            font-weight:900;
            letter-spacing:0;
            margin-top:30px;
            margin-bottom:18px;
            color:{text};
        }}

        .section-title.no-top-margin {{
            margin-top:0;
        }}

        .center-title {{
            text-align:center;
        }}

        .section-kicker {{
            font-size:18px;
            font-weight:900;
            color:{text};
            margin:14px 0 10px;
        }}

        .mini-label {{
            color:{muted};
            font-size:12px;
            text-transform:uppercase;
            letter-spacing:0.06em;
            font-weight:900;
            margin-bottom:8px;
        }}

        .small-muted {{
            color:{muted};
            font-size:15px;
            line-height:1.65;
            overflow-wrap:anywhere;
            white-space:normal;
        }}

        .gradient-text {{
            background:linear-gradient(90deg, {primary}, {accent}, {warm});
            -webkit-background-clip:text;
            -webkit-text-fill-color:transparent;
        }}
    """
