import streamlit as st


def inject_global_styles(theme: str):
    is_dark = theme == "Dark"

    bg = "#08111F" if is_dark else "#F8FAFC"
    card = "#111C2E" if is_dark else "#FFFFFF"
    card_2 = "#0C1728" if is_dark else "#EEF6FF"
    text = "#F8FAFC" if is_dark else "#0F172A"
    muted = "#A7B4C7" if is_dark else "#52627A"
    border = "#24344D" if is_dark else "#D9E4F2"
    primary = "#2563EB"
    accent = "#14B8A6"
    input_bg = "#0B1526" if is_dark else "#FFFFFF"
    input_text = "#F8FAFC" if is_dark else "#0F172A"
    soft_panel = "rgba(17,28,46,0.86)" if is_dark else "rgba(255,255,255,0.96)"
    nav_bg = "#0D182A" if is_dark else "#FFFFFF"
    shadow = "0 18px 48px rgba(0,0,0,0.24)" if is_dark else "0 18px 48px rgba(15,23,42,0.09)"

    st.markdown(
        f"""
        <style>
        html, body, [class*="css"] {{
            font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            font-size:16px;
        }}

        .stApp {{
            background:
                radial-gradient(circle at top left, rgba(37,99,235,0.16), transparent 30%),
                radial-gradient(circle at top right, rgba(20,184,166,0.15), transparent 28%),
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
            box-shadow:0 10px 24px rgba(15,23,42,0.10);
            white-space:nowrap !important;
        }}

        .stButton button[kind="primary"],
        .stDownloadButton button[kind="primary"] {{
            background:linear-gradient(135deg, {primary}, {accent}) !important;
            border-color:transparent !important;
            color:white !important;
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
            box-shadow:0 0 0 1px rgba(37,99,235,0.28) !important;
            outline:none !important;
        }}

        textarea::placeholder,
        input::placeholder {{
            color:{muted} !important;
            opacity:1 !important;
        }}

        .truthfit-navbar {{
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

        .truthfit-brand {{
            font-size:22px;
            font-weight:900;
            letter-spacing:-0.02em;
            color:{text};
        }}

        .truthfit-brand span {{
            color:{primary};
        }}

        .nav-subtitle {{
            color:{muted};
            font-size:13px;
            margin-top:2px;
        }}

        .page-header {{
            margin-top:18px;
            margin-bottom:22px;
        }}

        .page-header h1 {{
            font-size:34px;
            line-height:1.15;
            margin:0 0 8px;
            letter-spacing:-0.025em;
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
            letter-spacing:-0.025em;
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
            background:linear-gradient(90deg, {primary}, {accent});
            -webkit-background-clip:text;
            -webkit-text-fill-color:transparent;
        }}

        .hero {{
            padding:64px 44px;
            border:1px solid {border};
            border-radius:26px;
            background:
                linear-gradient(135deg, rgba(37,99,235,0.14), rgba(20,184,166,0.10)),
                {card};
            box-shadow:{shadow};
            animation:fadeInUp 0.5s ease;
        }}

        .hero h1 {{
            font-size:60px;
            line-height:1.03;
            letter-spacing:-0.04em;
            margin:0 0 18px;
            color:{text};
        }}

        .hero p {{
            font-size:19px;
            color:{muted};
            max-width:820px;
            line-height:1.65;
        }}

        .hero-split {{
            display:grid;
            grid-template-columns:minmax(0, 1.1fr) minmax(320px, 0.9fr);
            gap:36px;
            align-items:center;
        }}

        .hero-copy {{
            min-width:0;
        }}

        .hero-metrics {{
            display:grid;
            grid-template-columns:repeat(3, minmax(0, 1fr));
            gap:12px;
            margin-top:24px;
        }}

        .hero-metrics div {{
            padding:14px;
            border:1px solid {border};
            border-radius:14px;
            background:{soft_panel};
        }}

        .hero-metrics strong {{
            display:block;
            font-size:28px;
            color:{text};
            line-height:1;
        }}

        .hero-metrics span {{
            display:block;
            color:{muted};
            font-size:12px;
            margin-top:6px;
        }}

        .hero-visual {{
            position:relative;
            min-height:360px;
            border:1px solid {border};
            border-radius:22px;
            background:
                linear-gradient(145deg, rgba(20,184,166,0.16), rgba(37,99,235,0.12)),
                {card_2};
            overflow:hidden;
            box-shadow:{shadow};
        }}

        .resume-sheet {{
            position:absolute;
            inset:32px auto auto 34px;
            width:58%;
            min-height:260px;
            padding:22px;
            border-radius:16px;
            background:{card};
            border:1px solid {border};
            transform:rotate(-2deg);
        }}

        .sheet-top {{
            width:54px;
            height:54px;
            border-radius:50%;
            background:linear-gradient(135deg, {primary}, {accent});
            margin-bottom:18px;
        }}

        .sheet-line {{
            height:10px;
            width:72%;
            border-radius:999px;
            background:{border};
            margin:11px 0;
        }}

        .sheet-line.wide {{
            width:92%;
        }}

        .sheet-line.short {{
            width:46%;
        }}

        .sheet-section {{
            display:flex;
            gap:8px;
            margin:20px 0;
        }}

        .sheet-section span {{
            height:28px;
            flex:1;
            border-radius:999px;
            background:rgba(20,184,166,0.18);
            border:1px solid rgba(20,184,166,0.30);
        }}

        .ai-panel {{
            position:absolute;
            right:28px;
            top:78px;
            width:44%;
            display:flex;
            align-items:center;
            gap:14px;
            padding:18px;
            border-radius:18px;
            background:{soft_panel};
            border:1px solid {border};
            backdrop-filter:blur(16px);
        }}

        .ai-ring {{
            width:76px;
            height:76px;
            flex:0 0 76px;
            border-radius:50%;
            display:grid;
            place-items:center;
            font-weight:900;
            font-size:22px;
            color:{text};
            background:
                radial-gradient(circle at center, {card} 56%, transparent 57%),
                conic-gradient({accent} 0 82%, rgba(148,163,184,0.22) 82% 100%);
        }}

        .ai-panel strong {{
            display:block;
            color:{text};
            font-size:18px;
            margin-bottom:6px;
        }}

        .ai-panel span {{
            color:{muted};
            font-size:14px;
            line-height:1.45;
        }}

        .keyword-strip {{
            position:absolute;
            right:28px;
            bottom:42px;
            left:118px;
            display:flex;
            flex-wrap:wrap;
            gap:8px;
            justify-content:flex-end;
        }}

        .keyword-strip span {{
            padding:8px 11px;
            border-radius:999px;
            background:{card};
            border:1px solid {border};
            color:{text};
            font-size:12px;
            font-weight:800;
        }}

        .process-band {{
            display:grid;
            grid-template-columns:repeat(3, minmax(0, 1fr));
            gap:16px;
            padding:20px;
            border:1px solid {border};
            border-radius:20px;
            background:{card_2};
        }}

        .process-band h3 {{
            margin:10px 0 4px;
            color:{text};
        }}

        .process-band p {{
            color:{muted};
            margin:0;
            line-height:1.55;
            font-size:14px;
        }}

        .step-dot {{
            width:34px;
            height:34px;
            display:inline-grid;
            place-items:center;
            border-radius:50%;
            background:linear-gradient(135deg, {primary}, {accent});
            color:white !important;
            font-weight:900;
        }}

        .tf-card,
        .feature-card,
        .summary-card,
        .modern-info-card,
        .score-card,
        .verdict-card,
        .visual-note-card,
        .action-card {{
            border:1px solid {border};
            background:{card};
            box-shadow:{shadow};
            overflow-wrap:anywhere;
            white-space:normal;
        }}

        .tf-card,
        .feature-card {{
            padding:24px;
            border-radius:18px;
            height:100%;
            transition:transform 0.18s ease, border-color 0.18s ease;
        }}

        .tf-card:hover,
        .feature-card:hover,
        .modern-info-card:hover,
        .keyword-card:hover,
        .action-card:hover {{
            transform:translateY(-2px);
            border-color:rgba(37,99,235,0.62);
        }}

        .feature-card h3 {{
            font-size:20px;
            margin:0 0 10px;
        }}

        .feature-card p {{
            color:{muted};
            line-height:1.6;
            margin:0;
        }}

        .summary-card {{
            padding:22px;
            border-radius:18px;
            height:100%;
            background:{card_2};
        }}

        .summary-card h3 {{
            font-size:22px;
            margin:0 0 8px;
            line-height:1.25;
        }}

        .summary-card p {{
            color:{muted};
            margin:0;
            line-height:1.55;
        }}

        .verdict-card {{
            display:grid;
            grid-template-columns:minmax(0, 1fr) 260px;
            gap:22px;
            align-items:center;
            padding:28px;
            border-radius:22px;
            background:
                linear-gradient(135deg, rgba(37,99,235,0.16), rgba(20,184,166,0.10)),
                {card};
        }}

        .verdict-card h2 {{
            font-size:34px;
            line-height:1.15;
            margin:0 0 10px;
        }}

        .verdict-card p {{
            color:{muted};
            line-height:1.65;
            margin:0;
        }}

        .verdict-side {{
            padding:18px;
            border-radius:18px;
            border:1px solid {border};
            background:{soft_panel};
            display:flex;
            flex-direction:column;
            gap:8px;
            align-items:flex-start;
        }}

        .verdict-side strong {{
            font-size:36px;
            line-height:1;
        }}

        .verdict-side span:last-child {{
            color:{muted};
            font-size:14px;
            line-height:1.45;
        }}

        .recommendation-detail {{
            min-height:360px;
            display:flex;
            flex-direction:column;
            justify-content:center;
        }}

        .recommendation-detail h3 {{
            font-size:26px;
            margin:0 0 12px;
        }}

        .recommendation-detail p {{
            color:{muted};
            font-size:16px;
            line-height:1.65;
        }}

        .score-card {{
            padding:22px;
            border-radius:18px;
            min-height:178px;
        }}

        .score-value {{
            font-size:34px;
            font-weight:900;
            line-height:1;
            margin:6px 0 10px;
        }}

        .score-value span {{
            font-size:16px;
            color:{muted};
            margin-left:2px;
        }}

        .score-label {{
            font-weight:900;
            margin-bottom:6px;
        }}

        .score-card p {{
            color:{muted};
            line-height:1.45;
            margin:0;
            font-size:14px;
        }}

        .score-strong {{
            border-left:5px solid #22C55E;
        }}

        .score-good {{
            border-left:5px solid #14B8A6;
        }}

        .score-partial {{
            border-left:5px solid #F59E0B;
        }}

        .score-weak {{
            border-left:5px solid #EF4444;
        }}

        .chip {{
            display:inline-flex;
            align-items:center;
            justify-content:center;
            padding:8px 13px;
            margin:0;
            border-radius:999px;
            border:1px solid {border};
            background:{card_2};
            color:{text};
            font-size:13px;
            font-weight:800;
            max-width:100%;
            white-space:nowrap;
            overflow-wrap:normal;
            line-height:1.1;
            text-align:center;
            flex:0 0 auto;
        }}

        .chip-green {{
            border-color:rgba(34,197,94,0.45);
            background:rgba(34,197,94,0.13);
        }}

        .chip-yellow {{
            border-color:rgba(245,158,11,0.55);
            background:rgba(245,158,11,0.14);
        }}

        .chip-red {{
            border-color:rgba(239,68,68,0.55);
            background:rgba(239,68,68,0.14);
        }}

        .chip-blue {{
            border-color:rgba(59,130,246,0.45);
            background:rgba(59,130,246,0.13);
        }}

        .chip-cloud {{
            display:flex;
            flex-wrap:wrap;
            gap:6px;
        }}

        .sub-card-title {{
            text-align:center;
            font-size:22px;
            font-weight:900;
            margin-bottom:14px;
            color:{text};
        }}

        .balanced-stack {{
            display:grid;
            gap:14px;
        }}

        .balanced-item {{
            min-height:96px;
            display:flex;
            align-items:center;
            justify-content:center;
            text-align:left;
            padding:18px;
            border-radius:16px;
            font-size:15px;
            line-height:1.6;
            overflow-wrap:anywhere;
            white-space:normal;
        }}

        .balanced-item ul {{
            margin:0;
            padding-left:18px;
        }}

        .concern-item {{
            background:rgba(245,158,11,0.13);
            border:1px solid rgba(245,158,11,0.34);
        }}

        .strength-item {{
            background:rgba(34,197,94,0.13);
            border:1px solid rgba(34,197,94,0.34);
        }}

        .card-grid {{
            display:grid;
            grid-template-columns:repeat(2, minmax(0, 1fr));
            gap:18px;
            align-items:stretch;
        }}

        .card-grid-1 {{
            grid-template-columns:1fr;
        }}

        .modern-info-card {{
            padding:22px;
            border-radius:18px;
            min-height:100%;
            transition:transform 0.18s ease, border-color 0.18s ease;
        }}

        .modern-card-head {{
            display:flex;
            align-items:flex-start;
            justify-content:space-between;
            gap:14px;
            flex-wrap:wrap;
            margin-bottom:14px;
        }}

        .modern-card-head h4 {{
            margin:0;
            font-size:19px;
            line-height:1.35;
            color:{text};
            min-width:0;
            overflow-wrap:anywhere;
            flex:1 1 auto;
        }}

        .modern-card-head .chip {{
            margin-top:2px;
            max-width:100%;
            min-width:max-content;
        }}

        .modern-info-card .modern-card-head .chip,
        .action-card .modern-card-head .chip,
        .rewrite-card .modern-card-head .chip,
        .risk-card .modern-card-head .chip,
        .evidence-card .modern-card-head .chip {{
            order:2;
        }}

        .modern-info-card .modern-card-head h4,
        .action-card .modern-card-head h4,
        .rewrite-card .modern-card-head h4,
        .risk-card .modern-card-head h4,
        .evidence-card .modern-card-head h4 {{
            flex-basis:min(100%, 420px);
        }}

        .modern-info-row {{
            margin-top:14px;
            padding-top:12px;
            border-top:1px solid {border};
        }}

        .modern-info-row span {{
            display:block;
            color:{muted};
            font-size:12px;
            text-transform:uppercase;
            letter-spacing:0.05em;
            font-weight:900;
            margin-bottom:6px;
        }}

        .modern-info-row div,
        .modern-info-row p {{
            color:{text};
            font-size:15px;
            line-height:1.65;
            margin:0;
        }}

        .modern-info-row ul {{
            margin:4px 0 0 18px;
            padding:0;
        }}

        .modern-info-row li {{
            margin:5px 0;
        }}

        details {{
            margin-top:14px;
            padding-top:12px;
            border-top:1px solid {border};
        }}

        details summary {{
            cursor:pointer;
            color:{accent};
            font-weight:900;
            font-size:14px;
        }}

        .evidence-detail summary {{
            font-size:12px;
            text-transform:uppercase;
            letter-spacing:0.05em;
        }}

        .evidence-detail .modern-info-row {{
            border-top:0;
            margin-top:10px;
            padding-top:0;
        }}

        details p {{
            color:{text};
            line-height:1.65;
        }}

        .risk-card {{
            border-left:5px solid #F59E0B;
        }}

        .evidence-card {{
            border-left:5px solid {primary};
        }}

        .rewrite-card {{
            border-left:5px solid {accent};
        }}

        .compare-grid {{
            display:grid;
            grid-template-columns:1fr 1fr;
            gap:14px;
            margin-top:12px;
        }}

        .compare-grid div {{
            padding:16px;
            border:1px solid {border};
            border-radius:14px;
            background:{card_2};
        }}

        .compare-grid span {{
            display:block;
            color:{muted};
            font-size:12px;
            text-transform:uppercase;
            letter-spacing:0.05em;
            font-weight:900;
            margin-bottom:8px;
        }}

        .compare-grid p {{
            margin:0;
            color:{text};
            line-height:1.65;
        }}

        .ats-checklist-card {{
            margin-top:26px;
            padding:24px;
            border:1px solid {border};
            border-radius:22px;
            background:{card};
            box-shadow:{shadow};
        }}

        .keyword-grid {{
            display:grid;
            grid-template-columns:repeat(2, minmax(0, 1fr));
            gap:16px;
        }}

        .keyword-card {{
            padding:18px;
            border:1px solid {border};
            border-radius:18px;
            background:{card_2};
            transition:transform 0.18s ease, border-color 0.18s ease;
            min-height:150px;
            display:flex;
            flex-direction:column;
            justify-content:space-between;
        }}

        .keyword-card-top {{
            display:flex;
            justify-content:space-between;
            align-items:flex-start;
            gap:12px;
        }}

        .keyword-card h4 {{
            margin:0;
            font-size:18px;
            color:{text};
            line-height:1.3;
            min-width:0;
            overflow-wrap:anywhere;
        }}

        .keyword-card p {{
            color:{muted};
            margin:12px 0 0;
            line-height:1.6;
            font-size:14px;
        }}

        .keyword-badges {{
            display:flex;
            flex-direction:column;
            align-items:flex-end;
            gap:6px;
            min-width:128px;
            flex:0 0 auto;
        }}

        .priority-badge {{
            color:{text};
            font-size:12px;
            font-weight:900;
            text-transform:uppercase;
            letter-spacing:0.04em;
            opacity:0.9;
            white-space:nowrap;
        }}

        .visual-note-card {{
            padding:26px;
            border-radius:22px;
            min-height:300px;
            display:flex;
            flex-direction:column;
            justify-content:center;
        }}

        .visual-note-card h3 {{
            margin:0 0 10px;
            font-size:24px;
        }}

        .visual-note-card p {{
            color:{muted};
            line-height:1.65;
            margin:0;
        }}

        .action-grid {{
            display:grid;
            grid-template-columns:repeat(3, minmax(0, 1fr));
            gap:16px;
        }}

        .action-card {{
            display:flex;
            gap:16px;
            padding:20px;
            border-radius:18px;
            transition:transform 0.18s ease, border-color 0.18s ease;
            min-height:180px;
        }}

        .action-index {{
            width:38px;
            height:38px;
            flex:0 0 38px;
            display:grid;
            place-items:center;
            border-radius:50%;
            background:linear-gradient(135deg, {primary}, {accent});
            color:white;
            font-weight:900;
        }}

        .action-content {{
            min-width:0;
            flex:1;
        }}

        .action-content h4 {{
            margin:0;
            font-size:17px;
            line-height:1.35;
        }}

        .action-content p {{
            color:{muted};
            line-height:1.6;
            margin:10px 0;
        }}

        .source-label {{
            color:{accent};
            font-size:12px;
            font-weight:900;
            text-transform:uppercase;
            letter-spacing:0.05em;
        }}

        .stTabs [data-baseweb="tab-list"] {{
            gap:8px;
            border-bottom:1px solid {border};
            padding-bottom:8px;
            flex-wrap:wrap;
        }}

        .stTabs [data-baseweb="tab"] {{
            border-radius:12px;
            padding:10px 18px;
            background:{card};
            border:1px solid {border};
            font-size:15px;
            font-weight:800;
        }}

        @keyframes fadeInUp {{
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
            .action-grid,
            .compare-grid {{
                grid-template-columns:1fr;
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
        </style>
        """,
        unsafe_allow_html=True
    )
