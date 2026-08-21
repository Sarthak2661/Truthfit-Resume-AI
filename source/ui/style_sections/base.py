# ruff: noqa: F841,F541
def base_css(tokens: dict) -> str:
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

    return f"""        html, body, [class*="css"] {{
            font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            font-size:16px;
        }}

        .stApp {{
            background:
                radial-gradient(circle at top left, {primary_glow}, transparent 30%),
                radial-gradient(circle at top right, {accent_glow}, transparent 28%),
                radial-gradient(circle at 70% 85%, {warm_glow}, transparent 26%),
                {bg};
            color:{text};
        }}

        [data-testid="stHeader"] {{
            background:rgba(0,0,0,0);
        }}

        .block-container {{
            padding-top:1.2rem;
            padding-bottom:4rem;
            max-width:1240px;
        }}

        .stApp p,
        .stApp label,
        .stApp h1,
        .stApp h2,
        .stApp h3,
        .stApp h4 {{
            color:{text};
        }}

        label,
        [data-testid="stWidgetLabel"],
        [data-testid="stFileUploader"] label,
        [data-testid="stTextArea"] label,
        [data-testid="stToggle"] label {{
            color:{text} !important;
            opacity:1 !important;
        }}

        .stButton button,
        .stDownloadButton button {{
            border-radius:14px !important;
            min-height:46px;
            font-weight:800 !important;
            font-size:15px !important;
            border:1px solid {border} !important;
            color:{input_text} !important;
            background:{nav_bg} !important;
            box-shadow:0 8px 20px {"rgba(0,0,0,0.20)" if is_dark else "rgba(31,41,55,0.08)"};
            white-space:nowrap !important;
        }}

        .stButton button[kind="secondary"] {{
            background:{"#111A2D" if is_dark else "#FFFFFF"} !important;
            color:{text} !important;
            border-color:{border} !important;
        }}

        .stButton button[kind="primary"],
        .stDownloadButton button[kind="primary"] {{
            background:linear-gradient(135deg, {primary}, {accent}) !important;
            border-color:transparent !important;
            color:#FFFFFF !important;
        }}

        .stButton button:hover,
        .stDownloadButton button:hover {{
            border-color:{primary} !important;
        }}

        [data-testid="stSidebar"] {{
            background:{bg} !important;
        }}

        [data-testid="stSidebar"] * {{
            color:{text};
        }}

        .sidebar-demo-spacer {{
            min-height:clamp(80px, 28vh, 280px);
        }}

        [data-testid="stSelectbox"] [data-baseweb="select"],
        [data-testid="stSelectbox"] [data-baseweb="select"] > div,
        [data-testid="stSelectbox"] [data-baseweb="select"] div,
        [data-testid="stSelectbox"] [role="combobox"] {{
            background:{input_bg} !important;
            color:{input_text} !important;
            border-color:{border} !important;
        }}

        [data-testid="stSelectbox"] [data-baseweb="select"] > div {{
            border:1px solid {border} !important;
            border-radius:14px !important;
            box-shadow:none !important;
        }}

        [data-testid="stSelectbox"] svg,
        [data-testid="stTextInput"] svg {{
            color:{input_text} !important;
            fill:{input_text} !important;
        }}

        [data-testid="stTextInput"] > div,
        [data-testid="stTextInput"] [data-baseweb="input"],
        [data-testid="stTextInput"] [data-baseweb="input"] > div {{
            background:{input_bg} !important;
            color:{input_text} !important;
            border-color:{border} !important;
            border-radius:14px !important;
            box-shadow:none !important;
        }}

        [data-testid="stTextInput"] button {{
            background:{input_bg} !important;
            border-color:{border} !important;
            color:{input_text} !important;
        }}

        [data-testid="stElementContainer"]:has(.st-key-theme_toggle_switch) {{
            display:flex;
            justify-content:flex-end;
        }}

        .st-key-theme_toggle_switch {{
            display:flex;
            justify-content:flex-end;
            min-width:130px;
        }}

        .st-key-theme_toggle_switch label {{
            color:{text} !important;
            font-weight:800 !important;
            white-space:nowrap !important;
        }}

        .st-key-theme_toggle_switch [role="switch"] {{
            border-color:{border} !important;
        }}

        [data-testid="stDataFrame"],
        [data-testid="stDataEditor"] {{
            color:{text} !important;
        }}

        code,
        pre {{
            color:{text} !important;
            background:{card_2} !important;
        }}

        [data-testid="stFileUploader"] section {{
            background:{input_bg} !important;
            border:1px dashed {border} !important;
            border-radius:16px !important;
            color:{input_text} !important;
        }}

        [data-testid="stFileUploader"] section * {{
            color:{input_text} !important;
        }}

        [data-testid="stFileUploader"] button,
        [data-testid="stFileUploader"] div[role="button"] {{
            background:linear-gradient(135deg, {primary}, {accent}) !important;
            border:1px solid transparent !important;
            border-radius:12px !important;
            color:white !important;
            font-weight:800 !important;
        }}

        [data-testid="stFileUploader"] button *,
        [data-testid="stFileUploader"] div[role="button"] * {{
            color:white !important;
        }}

        [data-testid="stFileUploader"] [data-testid="stUploadedFile"],
        [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] {{
            background:{card_2} !important;
            border:1px solid {border} !important;
            border-radius:12px !important;
            color:{text} !important;
        }}

        [data-testid="stFileUploader"] [data-testid="stUploadedFile"] *,
        [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] *,
        [data-testid="stFileUploader"] small {{
            color:{text} !important;
        }}

        textarea,
        input {{
            background:{input_bg} !important;
            color:{input_text} !important;
            border:1px solid {border} !important;
            border-radius:14px !important;
            white-space:pre-wrap !important;
            overflow-wrap:anywhere !important;
            line-height:1.55 !important;
        }}

        textarea:focus,
        input:focus {{
            border-color:{primary} !important;
            box-shadow:0 0 0 1px {primary_glow} !important;
            outline:none !important;
        }}

        textarea::placeholder,
        input::placeholder {{
            color:{muted} !important;
            opacity:1 !important;
        }}
    """
