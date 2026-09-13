import os
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from apps.api.app.db.models import Base

DEFAULT_DATABASE_URL = "sqlite:///./.truthfit/truthfit.db"

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL).strip() or DEFAULT_DATABASE_URL


def get_engine() -> Engine:
    global _engine, _session_factory

    if _engine is None:
        url = database_url()
        if url.startswith("sqlite:///"):
            db_path = Path(url.replace("sqlite:///", "", 1))
            if db_path.parent != Path("."):
                db_path.parent.mkdir(parents=True, exist_ok=True)

        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        _engine = create_engine(url, connect_args=connect_args, pool_pre_ping=True)
        _session_factory = sessionmaker(bind=_engine, autoflush=False, autocommit=False, expire_on_commit=False)

    return _engine


def get_session_factory() -> sessionmaker[Session]:
    get_engine()
    return _session_factory


@contextmanager
def session_scope() -> Generator[Session]:
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    Base.metadata.create_all(bind=get_engine())


def check_database() -> bool:
    with get_engine().connect() as connection:
        connection.execute(text("SELECT 1"))
    return True


def configure_database_for_tests(url: str) -> None:
    global _engine, _session_factory

    if _engine is not None:
        _engine.dispose()

    os.environ["DATABASE_URL"] = url
    _engine = None
    _session_factory = None
    init_db()
