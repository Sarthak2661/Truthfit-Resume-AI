from datetime import UTC, datetime
from types import SimpleNamespace

from apps.api.app.services.analysis_service import _resume_versions


def _run(*, run_id: str, score: int, file_name: str, created_at: datetime):
    return SimpleNamespace(
        id=run_id,
        status="completed",
        overall_score=score,
        created_at=created_at,
        job=SimpleNamespace(title="Data Engineer", company="Northstar Analytics"),
        resume=SimpleNamespace(file_name=file_name),
    )


def test_resume_versions_compare_latest_resume_for_the_same_role():
    recent_first = [
        _run(
            run_id="new-run",
            score=84,
            file_name="resume-v2.docx",
            created_at=datetime(2026, 11, 2, tzinfo=UTC),
        ),
        _run(
            run_id="old-run",
            score=76,
            file_name="resume-v1.docx",
            created_at=datetime(2026, 10, 28, tzinfo=UTC),
        ),
    ]

    versions = _resume_versions(recent_first)

    assert versions == [
        {
            "role": "Data Engineer",
            "company": "Northstar Analytics",
            "resume_file_name": "resume-v2.docx",
            "latest_resume_file_name": "resume-v2.docx",
            "previous_resume_file_name": "resume-v1.docx",
            "runs": 2,
            "latest_score": 84,
            "best_score": 84,
            "change": 8,
            "latest_run_id": "new-run",
        }
    ]
