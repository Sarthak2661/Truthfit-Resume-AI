"""Create a PostgreSQL backup, restore it to an isolated database, and compare core counts."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from uuid import uuid4

from sqlalchemy.engine import make_url


CORE_TABLES = ("users", "resumes", "jobs", "analysis_runs", "evidence", "agent_events")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify that the configured PostgreSQL database can be backed up and restored."
    )
    parser.add_argument(
        "--database-url",
        default=os.getenv("DATABASE_URL", ""),
        help="PostgreSQL URL; defaults to DATABASE_URL.",
    )
    parser.add_argument(
        "--admin-database-url",
        default=os.getenv("TRUTHFIT_ADMIN_DATABASE_URL", ""),
        help=(
            "Optional PostgreSQL URL for creating and dropping the isolated restore database; "
            "defaults to the application database URL."
        ),
    )
    args = parser.parse_args()
    if not args.database_url:
        parser.error("Provide --database-url or set DATABASE_URL.")

    url = make_url(args.database_url)
    if not url.drivername.startswith("postgresql") or not url.database:
        parser.error("The backup/restore drill requires a PostgreSQL database URL.")
    admin_url = make_url(args.admin_database_url or args.database_url)
    if not admin_url.drivername.startswith("postgresql"):
        parser.error("The backup/restore admin URL must use PostgreSQL.")

    required = ("pg_dump", "createdb", "pg_restore", "psql", "dropdb")
    missing = [command for command in required if shutil.which(command) is None]
    if missing:
        parser.error(f"PostgreSQL client tools are missing: {', '.join(missing)}")

    restore_database = f"truthfit_restore_check_{uuid4().hex[:10]}"
    source_environment = {**os.environ, "PGPASSWORD": url.password or ""}
    admin_environment = {**os.environ, "PGPASSWORD": admin_url.password or ""}
    source_connection_args = _connection_args(url)
    admin_connection_args = _connection_args(admin_url)
    source_counts = _table_counts(url.database, source_connection_args, source_environment)

    with tempfile.TemporaryDirectory(prefix="truthfit-backup-") as temp_dir:
        backup_path = Path(temp_dir) / "truthfit.dump"
        _run(
            [
                "pg_dump",
                *source_connection_args,
                "--format=custom",
                "--no-owner",
                "--file",
                str(backup_path),
                url.database,
            ],
            source_environment,
        )
        created = False
        try:
            try:
                _run(["createdb", *admin_connection_args, restore_database], admin_environment)
            except subprocess.CalledProcessError as exc:
                raise RuntimeError(
                    "Could not create the isolated restore database. Set "
                    "TRUTHFIT_ADMIN_DATABASE_URL to a temporary PostgreSQL admin connection, "
                    "or grant CREATEDB only for the duration of this drill."
                ) from exc
            created = True
            _run(
                [
                    "pg_restore",
                    *admin_connection_args,
                    "--no-owner",
                    "--dbname",
                    restore_database,
                    str(backup_path),
                ],
                admin_environment,
            )
            restored_counts = _table_counts(
                restore_database,
                admin_connection_args,
                admin_environment,
            )
            if source_counts != restored_counts:
                raise RuntimeError(
                    f"Restore verification failed: source={source_counts}, restored={restored_counts}"
                )
        finally:
            if created:
                _run(
                    ["dropdb", *admin_connection_args, "--if-exists", restore_database],
                    admin_environment,
                )

    print(f"Backup/restore verified for {len(CORE_TABLES)} core tables: {source_counts}")
    return 0


def _connection_args(url) -> list[str]:
    arguments: list[str] = []
    if url.host:
        arguments.extend(["--host", url.host])
    if url.port:
        arguments.extend(["--port", str(url.port)])
    if url.username:
        arguments.extend(["--username", url.username])
    return arguments


def _table_counts(database: str, connection_args: list[str], environment: dict[str, str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for table in CORE_TABLES:
        result = _run(
            [
                "psql",
                *connection_args,
                "--dbname",
                database,
                "--tuples-only",
                "--no-align",
                "--command",
                f"SELECT COUNT(*) FROM {table}",
            ],
            environment,
            capture_output=True,
        )
        counts[table] = int(result.stdout.strip())
    return counts


def _run(
    command: list[str],
    environment: dict[str, str],
    capture_output: bool = False,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        env=environment,
        check=True,
        capture_output=capture_output,
        text=True,
    )


if __name__ == "__main__":
    raise SystemExit(main())
