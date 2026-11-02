"""add authenticated ownership

Revision ID: 0002_add_authenticated_ownership
Revises: 0001_create_truthfit_tables
Create Date: 2026-11-02
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0002_add_authenticated_ownership"
down_revision: str | None = "0001_create_truthfit_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("auth_subject", sa.String(length=255), nullable=True))
    op.execute("UPDATE users SET auth_subject = 'legacy:' || id")

    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column("auth_subject", existing_type=sa.String(length=255), nullable=False)
        batch_op.drop_index("ix_users_email")
        batch_op.create_index("ix_users_email", ["email"], unique=False)
        batch_op.create_index("ix_users_auth_subject", ["auth_subject"], unique=True)


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_index("ix_users_auth_subject")
        batch_op.drop_index("ix_users_email")
        batch_op.create_index("ix_users_email", ["email"], unique=True)
        batch_op.drop_column("auth_subject")
