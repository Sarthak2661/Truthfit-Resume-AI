import logging
import time
import uuid
from contextlib import contextmanager


LOGGER_NAME = "truthfit"


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def get_logger() -> logging.Logger:
    configure_logging()
    return logging.getLogger(LOGGER_NAME)


def new_request_id() -> str:
    return uuid.uuid4().hex[:10]


@contextmanager
def timed_operation(event: str, **fields):
    logger = get_logger()
    start = time.perf_counter()
    safe_fields = _format_fields(fields)
    logger.info("%s started%s", event, safe_fields)

    try:
        yield
    except Exception as exc:
        duration_ms = int((time.perf_counter() - start) * 1000)
        logger.exception(
            "%s failed duration_ms=%s error_type=%s%s",
            event,
            duration_ms,
            exc.__class__.__name__,
            safe_fields,
        )
        raise
    else:
        duration_ms = int((time.perf_counter() - start) * 1000)
        logger.info("%s completed duration_ms=%s%s", event, duration_ms, safe_fields)


def log_event(event: str, **fields) -> None:
    get_logger().info("%s%s", event, _format_fields(fields))


def log_warning(event: str, **fields) -> None:
    get_logger().warning("%s%s", event, _format_fields(fields))


def _format_fields(fields: dict) -> str:
    if not fields:
        return ""

    clean_fields = {
        key: value
        for key, value in fields.items()
        if value is not None and key not in {"api_key", "prompt", "resume_text", "job_description"}
    }

    if not clean_fields:
        return ""

    return " " + " ".join(f"{key}={value}" for key, value in clean_fields.items())
