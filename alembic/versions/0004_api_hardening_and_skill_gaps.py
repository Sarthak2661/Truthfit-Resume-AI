"""add idempotency and normalized skill gaps

Revision ID: 0004_api_hardening
Revises: 0003_privacy_and_retention
Create Date: 2026-11-03
"""

from collections.abc import Sequence
from datetime import datetime, timezone
import json
from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision: str = "0004_api_hardening"
down_revision: str | None = "0003_privacy_and_retention"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("analysis_runs") as batch_op:
        batch_op.add_column(sa.Column("idempotency_key", sa.String(length=128), nullable=True))
        batch_op.add_column(sa.Column("request_fingerprint", sa.String(length=64), nullable=True))
        batch_op.create_unique_constraint(
            "uq_analysis_runs_user_id_idempotency_key",
            ["user_id", "idempotency_key"],
        )

    op.create_table(
        "skill_gaps",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("analysis_run_id", sa.String(length=32), nullable=False),
        sa.Column("user_id", sa.String(length=32), nullable=False),
        sa.Column("normalized_skill", sa.String(length=255), nullable=False),
        sa.Column("display_skill", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["analysis_run_id"], ["analysis_runs.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "analysis_run_id",
            "normalized_skill",
            name="uq_skill_gaps_run_skill",
        ),
    )
    op.create_index("ix_skill_gaps_analysis_run_id", "skill_gaps", ["analysis_run_id"])
    op.create_index("ix_skill_gaps_user_id", "skill_gaps", ["user_id"])
    op.create_index("ix_skill_gaps_normalized_skill", "skill_gaps", ["normalized_skill"])
    _backfill_skill_gaps()


def downgrade() -> None:
    op.drop_index("ix_skill_gaps_normalized_skill", table_name="skill_gaps")
    op.drop_index("ix_skill_gaps_user_id", table_name="skill_gaps")
    op.drop_index("ix_skill_gaps_analysis_run_id", table_name="skill_gaps")
    op.drop_table("skill_gaps")
    with op.batch_alter_table("analysis_runs") as batch_op:
        batch_op.drop_constraint("uq_analysis_runs_user_id_idempotency_key", type_="unique")
        batch_op.drop_column("request_fingerprint")
        batch_op.drop_column("idempotency_key")


def _backfill_skill_gaps() -> None:
    connection = op.get_bind()
    rows = connection.execute(
        sa.text(
            "SELECT id, user_id, result_json, created_at FROM analysis_runs "
            "WHERE status = 'completed'"
        )
    ).mappings()
    records = []
    for row in rows:
        result = row["result_json"] or {}
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except json.JSONDecodeError:
                continue
        missing = result.get("skills_analysis", {}).get("missing_skills", [])
        unique_skills: dict[str, str] = {}
        for item in missing:
            raw_skill = item.get("skill") or item.get("requirement") if isinstance(item, dict) else item
            display = " ".join(str(raw_skill or "").split())[:255]
            if display:
                unique_skills.setdefault(display.casefold(), display)
        for normalized, display in unique_skills.items():
            records.append(
                {
                    "id": uuid4().hex,
                    "analysis_run_id": row["id"],
                    "user_id": row["user_id"],
                    "normalized_skill": normalized,
                    "display_skill": display,
                    "created_at": row["created_at"] or datetime.now(timezone.utc),
                }
            )

    if records:
        skill_gaps = sa.table(
            "skill_gaps",
            sa.column("id", sa.String),
            sa.column("analysis_run_id", sa.String),
            sa.column("user_id", sa.String),
            sa.column("normalized_skill", sa.String),
            sa.column("display_skill", sa.String),
            sa.column("created_at", sa.DateTime(timezone=True)),
        )
        op.bulk_insert(skill_gaps, records)
