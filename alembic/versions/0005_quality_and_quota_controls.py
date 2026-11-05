"""add atomic quota, consent, and analysis telemetry fields

Revision ID: 0005_quality_controls
Revises: 0004_api_hardening
Create Date: 2026-11-04
"""

from collections import Counter
from collections.abc import Sequence
from datetime import date, datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision: str = "0005_quality_controls"
down_revision: str | None = "0004_api_hardening"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "daily_analysis_usage",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("user_id", sa.String(length=32), nullable=False),
        sa.Column("usage_date", sa.Date(), nullable=False),
        sa.Column("used_count", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "usage_date",
            name="uq_daily_analysis_usage_user_date",
        ),
    )
    op.create_index("ix_daily_analysis_usage_user_id", "daily_analysis_usage", ["user_id"])
    op.create_index("ix_daily_analysis_usage_usage_date", "daily_analysis_usage", ["usage_date"])

    with op.batch_alter_table("analysis_runs") as batch_op:
        batch_op.add_column(
            sa.Column("prompt_version", sa.String(length=32), server_default="v1", nullable=False)
        )
        batch_op.add_column(
            sa.Column("schema_version", sa.String(length=32), server_default="v1", nullable=False)
        )
        batch_op.add_column(sa.Column("consent_version", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("consented_at", sa.DateTime(timezone=True), nullable=True))

    with op.batch_alter_table("agent_events") as batch_op:
        batch_op.add_column(sa.Column("input_tokens", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("output_tokens", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("estimated_cost_micros", sa.Integer(), nullable=True))

    _backfill_daily_usage()


def downgrade() -> None:
    with op.batch_alter_table("agent_events") as batch_op:
        batch_op.drop_column("estimated_cost_micros")
        batch_op.drop_column("output_tokens")
        batch_op.drop_column("input_tokens")

    with op.batch_alter_table("analysis_runs") as batch_op:
        batch_op.drop_column("consented_at")
        batch_op.drop_column("consent_version")
        batch_op.drop_column("schema_version")
        batch_op.drop_column("prompt_version")

    op.drop_index("ix_daily_analysis_usage_usage_date", table_name="daily_analysis_usage")
    op.drop_index("ix_daily_analysis_usage_user_id", table_name="daily_analysis_usage")
    op.drop_table("daily_analysis_usage")


def _backfill_daily_usage() -> None:
    connection = op.get_bind()
    rows = connection.execute(sa.text("SELECT user_id, created_at FROM analysis_runs")).mappings()
    counts: Counter[tuple[str, date]] = Counter()
    for row in rows:
        created_at = row["created_at"]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        usage_date = created_at.date() if created_at else datetime.now(timezone.utc).date()
        counts[(row["user_id"], usage_date)] += 1

    if not counts:
        return

    usage_table = sa.table(
        "daily_analysis_usage",
        sa.column("id", sa.String),
        sa.column("user_id", sa.String),
        sa.column("usage_date", sa.Date),
        sa.column("used_count", sa.Integer),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    now = datetime.now(timezone.utc)
    op.bulk_insert(
        usage_table,
        [
            {
                "id": uuid4().hex,
                "user_id": user_id,
                "usage_date": usage_date,
                "used_count": used_count,
                "updated_at": now,
            }
            for (user_id, usage_date), used_count in counts.items()
        ],
    )
