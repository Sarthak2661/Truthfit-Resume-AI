from source.loaders.text_extractors import extract_docx_text, extract_pdf_text
from source.loaders.validation import validate_upload_size


def extract_jd_text(uploaded_file, pasted_text: str) -> str:
    """
    Combines uploaded JD text and pasted JD text.
    User can upload a JD file, paste a JD, or use both.
    """
    text_parts = []

    if uploaded_file is not None:
        validate_upload_size(uploaded_file, "Job description")
        file_name = uploaded_file.name.lower()

        if file_name.endswith(".pdf"):
            text_parts.append(extract_pdf_text(uploaded_file, "Job description"))

        elif file_name.endswith(".docx"):
            text_parts.append(extract_docx_text(uploaded_file))

        elif file_name.endswith(".txt"):
            text_parts.append(uploaded_file.read().decode("utf-8", errors="ignore"))

        else:
            raise ValueError("Unsupported JD file type. Use PDF, DOCX, or TXT.")

    if pasted_text and pasted_text.strip():
        text_parts.append(pasted_text.strip())

    return "\n\n".join(text_parts).strip()

