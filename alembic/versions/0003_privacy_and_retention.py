"""add privacy retention controls

Revision ID: 0003_privacy_and_retention
Revises: 0002_add_authenticated_ownership
Create Date: 2026-11-03
"""

from collections.abc import Sequence
from datetime import datetime, timedelta

from alembic import op
import sqlalchemy as sa

revision: str = "0003_privacy_and_retention"
down_revision: str | None = "0002_add_authenticated_ownership"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("resumes") as batch_op:
        batch_op.alter_column("parsed_text", existing_type=sa.Text(), nullable=True)
        batch_op.add_column(sa.Column("encrypted_original", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("encryption_nonce", sa.String(length=255), nullable=True))
        batch_op.add_column(
            sa.Column("original_retained", sa.Boolean(), nullable=False, server_default=sa.false())
        )

    # Legacy parsed_text may contain unredacted resumes. Redacted copies remain available.
    op.execute("UPDATE resumes SET parsed_text = NULL")

    op.add_column("analysis_runs", sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))
    connection = op.get_bind()
    rows = connection.execute(sa.text("SELECT id, created_at FROM analysis_runs")).mappings()
    for row in rows:
        created_at = row["created_at"]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        connection.execute(
            sa.text("UPDATE analysis_runs SET expires_at = :expires_at WHERE id = :run_id"),
            {"expires_at": created_at + timedelta(days=30), "run_id": row["id"]},
        )
    with op.batch_alter_table("analysis_runs") as batch_op:
        batch_op.alter_column("expires_at", existing_type=sa.DateTime(timezone=True), nullable=False)
        batch_op.create_index("ix_analysis_runs_expires_at", ["expires_at"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("analysis_runs") as batch_op:
        batch_op.drop_index("ix_analysis_runs_expires_at")
        batch_op.drop_column("expires_at")
    with op.batch_alter_table("resumes") as batch_op:
        batch_op.drop_column("original_retained")
        batch_op.drop_column("encryption_nonce")
        batch_op.drop_column("encrypted_original")
        batch_op.alter_column("parsed_text", existing_type=sa.Text(), nullable=False)
