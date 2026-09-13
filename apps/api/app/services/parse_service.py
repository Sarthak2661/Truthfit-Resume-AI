from dataclasses import dataclass
from io import BytesIO

from fastapi import UploadFile

from apps.api.app.schemas import JobParseResponse, ResumeParseResponse
from source.loaders.jd_loader import extract_jd_text
from source.loaders.resume_loader import extract_text_from_file
from source.services.observability import timed_operation
from source.services.resume_heatmap import redact_personal_details
from source.services.url_utils import normalize_http_url


@dataclass
class UploadedBytes:
    content: bytes
    name: str

    @property
    def size(self) -> int:
        return len(self.content)

    def read(self, *args, **kwargs) -> bytes:
        return self._buffer.read(*args, **kwargs)

    def seek(self, *args, **kwargs):
        return self._buffer.seek(*args, **kwargs)

    def tell(self) -> int:
        return self._buffer.tell()

    def seekable(self) -> bool:
        return True

    def readable(self) -> bool:
        return True

    def __post_init__(self):
        self._buffer = BytesIO(self.content)


async def _to_uploaded_bytes(file: UploadFile | None) -> UploadedBytes | None:
    if file is None:
        return None

    content = await file.read()
    return UploadedBytes(content=content, name=file.filename or "uploaded.txt")


async def parse_resume(file: UploadFile, request_id: str) -> ResumeParseResponse:
    uploaded = await _to_uploaded_bytes(file)

    with timed_operation("api_resume_parse", request_id=request_id, file_type=_file_type(uploaded.name)):
        text = extract_text_from_file(uploaded)
        redacted_text = redact_personal_details(text)

    return ResumeParseResponse(
        request_id=request_id,
        filename=uploaded.name,
        text=text,
        redacted_text=redacted_text,
        char_count=len(text),
        redacted_char_count=len(redacted_text),
    )


async def parse_job_description(
    file: UploadFile | None,
    pasted_text: str,
    job_link: str,
    request_id: str,
) -> JobParseResponse:
    uploaded = await _to_uploaded_bytes(file)
    filename = uploaded.name if uploaded else None

    with timed_operation("api_job_parse", request_id=request_id, file_type=_file_type(filename or "text")):
        text = extract_jd_text(uploaded, pasted_text)
        normalized_link = normalize_http_url(job_link)

    return JobParseResponse(
        request_id=request_id,
        filename=filename,
        text=text,
        char_count=len(text),
        job_link=normalized_link,
    )


def _file_type(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else "text"
