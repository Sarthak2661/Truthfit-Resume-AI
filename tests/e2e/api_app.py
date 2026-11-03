import os
from pathlib import Path

from fastapi import Header, HTTPException

ROOT_DIR = Path(__file__).resolve().parents[2]
DATABASE_PATH = ROOT_DIR / ".truthfit" / "e2e.db"
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
DATABASE_PATH.unlink(missing_ok=True)

os.environ["TRUTHFIT_ENV"] = "test"
os.environ["TRUTHFIT_ANALYSIS_QUEUE"] = "background"
os.environ["TRUTHFIT_RATE_LIMIT_BACKEND"] = "memory"
os.environ["TRUTHFIT_ALLOWED_ORIGINS"] = "http://127.0.0.1:3010,http://localhost:3010"

from apps.api.app.auth import CurrentUser, get_current_user  # noqa: E402
from apps.api.app.db import repositories  # noqa: E402
from apps.api.app.db.database import (  # noqa: E402
    configure_database_for_tests,
    session_scope,
)
from apps.api.app.main import create_app  # noqa: E402
from apps.api.app.services import analysis_service  # noqa: E402
from source.services.sample_analysis import sample_analysis_result  # noqa: E402


configure_database_for_tests(f"sqlite:///{DATABASE_PATH.as_posix()}")
with session_scope() as session:
    repositories.get_or_create_user(
        session,
        auth_subject="e2e-user",
        email="e2e@truthfit.local",
    )


def _fixture_analysis(**_kwargs) -> dict:
    return sample_analysis_result()


def _e2e_user(authorization: str | None = Header(default=None)) -> CurrentUser:
    if authorization != "Bearer truthfit-e2e-token":
        raise HTTPException(status_code=401, detail="Authentication is required.")
    return CurrentUser(subject="e2e-user", email="e2e@truthfit.local")


analysis_service.generate_resume_analysis = _fixture_analysis
app = create_app()
app.dependency_overrides[get_current_user] = _e2e_user
