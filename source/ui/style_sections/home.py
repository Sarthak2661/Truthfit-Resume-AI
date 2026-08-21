# ruff: noqa: F841,F541
def home_css(tokens: dict) -> str:
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

    return f"""        .hero {{
            padding:64px 44px;
            border:1px solid {border};
            border-radius:26px;
            background:
                linear-gradient(135deg, {primary_glow}, {accent_glow} 52%, {warm_glow}),
                {card};
            box-shadow:{shadow};
            animation:fadeInUp 0.5s ease;
        }}

        .hero h1 {{
            font-size:60px;
            line-height:1.03;
            letter-spacing:0;
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
                linear-gradient(145deg, {accent_glow}, {primary_glow}),
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
            background:{accent_glow};
            border:1px solid {border};
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
    """
