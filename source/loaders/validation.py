MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_PDF_PAGES = 8


def validate_upload_size(uploaded_file, label: str) -> None:
    size = getattr(uploaded_file, "size", None)

    if size is None and hasattr(uploaded_file, "getbuffer"):
        size = len(uploaded_file.getbuffer())

    if size is not None and size > MAX_UPLOAD_BYTES:
        max_mb = MAX_UPLOAD_BYTES // (1024 * 1024)
        raise ValueError(f"{label} file is too large. Use a file under {max_mb} MB.")


def validate_pdf_page_count(reader, label: str) -> None:
    page_count = len(reader.pages)

    if page_count > MAX_PDF_PAGES:
        raise ValueError(
            f"{label} PDF has {page_count} pages. Use a concise file with {MAX_PDF_PAGES} pages or fewer."
        )
