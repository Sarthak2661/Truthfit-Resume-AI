from concurrent.futures import ThreadPoolExecutor
from datetime import date

import pytest

from apps.api.app.db import repositories
from apps.api.app.db.database import (
    assert_database_schema_current,
    configure_database_for_tests,
    session_scope,
)


def test_durable_database_rejects_unversioned_schema(monkeypatch, tmp_path):
    database = tmp_path / "unversioned.db"
    configure_database_for_tests(f"sqlite:///{database.as_posix()}")
    monkeypatch.setenv("TRUTHFIT_ENV", "production")

    with pytest.raises(RuntimeError, match="alembic upgrade head"):
        assert_database_schema_current()


def test_daily_quota_increment_is_atomic(monkeypatch, tmp_path):
    database = tmp_path / "quota.db"
    configure_database_for_tests(f"sqlite:///{database.as_posix()}")
    with session_scope() as session:
        user = repositories.get_or_create_user(
            session,
            auth_subject="quota-concurrency-user",
            email="quota@example.com",
        )
        user_id = user.id

    def consume() -> int | None:
        with session_scope() as session:
            return repositories.consume_daily_analysis_quota(
                session,
                user_id,
                date(2026, 11, 4),
                limit=3,
            )

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: consume(), range(8)))

    accepted = sorted(result for result in results if result is not None)
    assert accepted == [1, 2, 3]
    assert results.count(None) == 5
