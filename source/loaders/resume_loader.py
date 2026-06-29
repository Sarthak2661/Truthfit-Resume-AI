from pypdf import PdfReader
from docx import Document


def extract_text_from_file(uploaded_file) -> str:
    """
    Extracts text from PDF, DOCX, or TXT resume files.
    """
    if uploaded_file is None:
        return ""

    file_name = uploaded_file.name.lower()

    if file_name.endswith(".pdf"):
        return extract_pdf_text(uploaded_file)

    if file_name.endswith(".docx"):
        return extract_docx_text(uploaded_file)

    if file_name.endswith(".txt"):
        return uploaded_file.read().decode("utf-8", errors="ignore")

    raise ValueError("Unsupported resume file type. Use PDF, DOCX, or TXT.")


def extract_pdf_text(uploaded_file) -> str:
    reader = PdfReader(uploaded_file)
    text = []

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text.append(page_text)

    return "\n".join(text).strip()


def extract_docx_text(uploaded_file) -> str:
    doc = Document(uploaded_file)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs).strip()