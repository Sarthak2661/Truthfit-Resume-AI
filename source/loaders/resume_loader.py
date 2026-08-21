from source.loaders.text_extractors import extract_docx_text, extract_pdf_text
from source.loaders.validation import validate_upload_size


def extract_text_from_file(uploaded_file) -> str:
    """
    Extracts text from PDF, DOCX, or TXT resume files.
    """
    if uploaded_file is None:
        return ""

    validate_upload_size(uploaded_file, "Resume")
    file_name = uploaded_file.name.lower()

    if file_name.endswith(".pdf"):
        return extract_pdf_text(uploaded_file, "Resume")

    if file_name.endswith(".docx"):
        return extract_docx_text(uploaded_file)

    if file_name.endswith(".txt"):
        return uploaded_file.read().decode("utf-8", errors="ignore")

    raise ValueError("Unsupported resume file type. Use PDF, DOCX, or TXT.")

