from docx import Document
from pypdf import PdfReader

from source.loaders.validation import validate_pdf_page_count


def extract_pdf_text(uploaded_file, label: str) -> str:
    reader = PdfReader(uploaded_file)
    validate_pdf_page_count(reader, label)
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
