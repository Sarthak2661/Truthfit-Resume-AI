def theme_tokens(theme: str) -> dict:
    is_dark = theme == "Dark"

    return {
        "is_dark": is_dark,
        "bg": "#070A12" if is_dark else "#F6F8FC",
        "card": "#101828" if is_dark else "#FFFFFF",
        "card_2": "#172033" if is_dark else "#EEF3FF",
        "text": "#F8FAFC" if is_dark else "#111827",
        "muted": "#A7B2C7" if is_dark else "#5B6475",
        "border": "#2B3752" if is_dark else "#D8E0EE",
        "primary": "#7C8CFF" if is_dark else "#355CFF",
        "accent": "#35D6C6" if is_dark else "#0EA5A3",
        "warm": "#FFB454" if is_dark else "#F97316",
        "input_bg": "#0B1220" if is_dark else "#FFFFFF",
        "input_text": "#F8FAFC" if is_dark else "#111827",
        "soft_panel": "rgba(16,24,40,0.88)" if is_dark else "rgba(255,255,255,0.94)",
        "nav_bg": "#0D1526" if is_dark else "#FFFFFF",
        "shadow": "0 22px 58px rgba(0,0,0,0.38)" if is_dark else "0 20px 50px rgba(31,41,55,0.11)",
        "primary_glow": "rgba(124,140,255,0.18)" if is_dark else "rgba(53,92,255,0.10)",
        "accent_glow": "rgba(53,214,198,0.13)" if is_dark else "rgba(14,165,163,0.10)",
        "warm_glow": "rgba(255,180,84,0.12)" if is_dark else "rgba(249,115,22,0.08)",
    }
