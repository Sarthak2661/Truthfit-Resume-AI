import html
import re
import textwrap
from uuid import uuid4

import bleach
import streamlit as st


ALLOWED_TEXT_TAGS = ["br", "li", "ol", "p", "summary", "ul"]


def unique_chart_key(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


def render_html(markup: str):
    cleaned_markup = textwrap.dedent(markup).strip()

    if hasattr(st, "html"):
        st.html(cleaned_markup)
    else:
        st.markdown(cleaned_markup, unsafe_allow_html=True)


def clean_value(value) -> str:
    if value is None:
        return ""

    if isinstance(value, list):
        return "\n".join([f"- {clean_value(v)}" for v in value if clean_value(v)])

    if isinstance(value, dict):
        return "\n".join(
            [
                f"{str(k).replace('_', ' ').title()}: {clean_value(v)}"
                for k, v in value.items()
                if clean_value(v)
            ]
        )

    text = str(value)
    text = text.replace('\\"', '"').replace("\\'", "'")
    text = text.replace("\\n", "\n").replace("\\/", "/")

    for _ in range(3):
        unescaped = html.unescape(text)
        if unescaped == text:
            break
        text = unescaped

    text = re.sub(r"```(?:html|json|text|markdown)?", "", text, flags=re.IGNORECASE)
    text = text.replace("```", "")
    text = re.sub(r"<\s*summary[^>]*>", "Summary: ", text, flags=re.IGNORECASE)
    text = re.sub(r"</?\s*(div|span|strong|em|h[1-6]|details|tr|td|th)[^>]*>", " ", text, flags=re.IGNORECASE)
    text = bleach.clean(text, tags=ALLOWED_TEXT_TAGS, attributes={}, strip=True)
    text = re.sub(r"<\s*li[^>]*>", "- ", text, flags=re.IGNORECASE)
    text = re.sub(r"</\s*li\s*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<\s*br\s*/?\s*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</\s*(p|summary|ul|ol)\s*>", "\n", text, flags=re.IGNORECASE)
    text = bleach.clean(text, tags=[], attributes={}, strip=True)
    text = html.unescape(text)
    text = text.replace("`", "")

    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"\b[Aa]sk user\b", "Ask the candidate", text)
    text = re.sub(r"\b[Aa]sk the user\b", "Ask the candidate", text)
    text = re.sub(r"\b[Tt]he user\b", "the candidate", text)
    text = re.sub(r"\b[Uu]ser\b", "candidate", text)

    return text.strip()


def normalize_analysis_result(value):
    if isinstance(value, dict):
        return {key: normalize_analysis_result(item) for key, item in value.items()}

    if isinstance(value, list):
        return [normalize_analysis_result(item) for item in value]

    if isinstance(value, str):
        return clean_value(value)

    return value


def bullet_text(value) -> str:
    text = clean_value(value)

    if not text:
        return ""

    lines = [line.strip() for line in text.splitlines() if line.strip()]

    if len(lines) > 1:
        normalized = []
        for line in lines:
            if line.startswith("- "):
                normalized.append(f"- {line[2:].strip()}")
            else:
                normalized.append(f"- {line}")
        return "\n".join(normalized)

    return lines[0] if lines else ""


def display_text(value) -> str:
    return bullet_text(value) or clean_value(value)


def friendly_label(value) -> str:
    text = clean_value(value)
    mapping = {
        "High": "Important",
        "Medium": "Would help",
        "Low": "Nice to have",
        "high": "Important",
        "medium": "Would help",
        "low": "Nice to have",
        "Partial": "Needs proof",
        "Unsafe": "Do not claim",
        "Missing": "Missing",
        "Supported": "Supported",
        "Covered": "Covered",
        "Strong": "Strong",
        "Weak": "Weak",
        "Good Match": "Good Match",
        "Strong Match": "Strong Match",
        "Partial Match": "Partial Match",
        "Weak Match": "Weak Match",
    }
    return mapping.get(text, text)


def display_field_value(label: str, value) -> str:
    if label.lower() in [
        "priority",
        "action level",
        "severity",
        "attention",
        "status",
        "coverage status",
        "evidence status",
        "match strength",
    ]:
        return friendly_label(value)
    return display_text(value)


def friendly_field_label(label: str) -> str:
    mapping = {
        "Priority": "Action Level",
        "Severity": "Attention",
        "Resume Evidence": "Profile Evidence",
        "Jd Evidence": "JD Evidence",
        "Why It Helps": "Why This Helps",
        "Why Needed": "Why This Matters",
    }
    return mapping.get(label, label)


def text_to_html(value) -> str:
    text = display_text(value)

    if not text:
        return ""

    lines = [line.strip() for line in text.splitlines() if line.strip()]

    if len(lines) > 1 or any(line.startswith("- ") for line in lines):
        return "<ul>" + "".join(
            f"<li>{html.escape(line[2:] if line.startswith('- ') else line)}</li>"
            for line in lines
        ) + "</ul>"

    return html.escape(text)


# -------------------------------------------------
# Status / score helpers
# -------------------------------------------------


def status_to_chip_class(status: str) -> str:
    status = (status or "").lower()

    if status in [
        "supported",
        "covered",
        "strong",
        "strong match",
        "low",
        "nice to have",
        "apply confidently",
    ]:
        return "chip-green"

    if status in [
        "partial",
        "needs proof",
        "good match",
        "medium",
        "would help",
        "apply after tailoring",
    ]:
        return "chip-yellow"

    if status in [
        "missing",
        "unsafe",
        "weak",
        "weak match",
        "high",
        "important",
        "skip",
        "high risk",
        "important risk",
    ]:
        return "chip-red"

    return "chip-blue"


def severity_rank(status: str) -> int:
    status = (status or "").lower()

    if status in ["high", "important", "missing", "unsafe", "weak"]:
        return 0

    if status in ["medium", "would help", "partial", "needs proof"]:
        return 1

    if status in ["low", "nice to have", "supported", "covered", "strong"]:
        return 2

    return 3


def get_score_label(score: int) -> str:
    if score >= 85:
        return "Strong Match"
    if score >= 70:
        return "Good Match"
    if score >= 50:
        return "Partial Match"
    return "Weak Match"


def get_score_meaning(score: int) -> str:
    if score >= 85:
        return "Apply confidently"
    if score >= 70:
        return "Apply after tailoring"
    if score >= 50:
        return "Improve resume first"
    return "The skill gap is high"


def get_score_class(score: int) -> str:
    if score >= 85:
        return "score-strong"
    if score >= 70:
        return "score-good"
    if score >= 50:
        return "score-partial"
    return "score-weak"


# -------------------------------------------------
# Chart helpers
# -------------------------------------------------


def is_dark_theme() -> bool:
    return st.session_state.get("theme", "Dark") == "Dark"

