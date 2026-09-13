"""create truthfit tables

Revision ID: 0001_create_truthfit_tables
Revises:
Create Date: 2026-09-09
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0001_create_truthfit_tables"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "jobs",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("user_id", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("company", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_jobs_user_id"), "jobs", ["user_id"], unique=False)

    op.create_table(
        "resumes",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("user_id", sa.String(length=32), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("parsed_text", sa.Text(), nullable=False),
        sa.Column("redacted_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_resumes_user_id"), "resumes", ["user_id"], unique=False)

    op.create_table(
        "analysis_runs",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("user_id", sa.String(length=32), nullable=False),
        sa.Column("resume_id", sa.String(length=32), nullable=False),
        sa.Column("job_id", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("model", sa.String(length=120), nullable=False),
        sa.Column("overall_score", sa.Integer(), nullable=False),
        sa.Column("result_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"]),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_analysis_runs_job_id"), "analysis_runs", ["job_id"], unique=False)
    op.create_index(op.f("ix_analysis_runs_resume_id"), "analysis_runs", ["resume_id"], unique=False)
    op.create_index(op.f("ix_analysis_runs_status"), "analysis_runs", ["status"], unique=False)
    op.create_index(op.f("ix_analysis_runs_user_id"), "analysis_runs", ["user_id"], unique=False)

    op.create_table(
        "agent_events",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("analysis_run_id", sa.String(length=32), nullable=False),
        sa.Column("agent_name", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("error_type", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["analysis_run_id"], ["analysis_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_agent_events_analysis_run_id"), "agent_events", ["analysis_run_id"], unique=False)

    op.create_table(
        "evidence",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("analysis_run_id", sa.String(length=32), nullable=False),
        sa.Column("requirement", sa.Text(), nullable=False),
        sa.Column("resume_evidence", sa.Text(), nullable=False),
        sa.Column("evidence_type", sa.String(length=80), nullable=False),
        sa.Column("confidence", sa.String(length=40), nullable=False),
        sa.Column("verified", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["analysis_run_id"], ["analysis_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_evidence_analysis_run_id"), "evidence", ["analysis_run_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_evidence_analysis_run_id"), table_name="evidence")
    op.drop_table("evidence")
    op.drop_index(op.f("ix_agent_events_analysis_run_id"), table_name="agent_events")
    op.drop_table("agent_events")
    op.drop_index(op.f("ix_analysis_runs_user_id"), table_name="analysis_runs")
    op.drop_index(op.f("ix_analysis_runs_status"), table_name="analysis_runs")
    op.drop_index(op.f("ix_analysis_runs_resume_id"), table_name="analysis_runs")
    op.drop_index(op.f("ix_analysis_runs_job_id"), table_name="analysis_runs")
    op.drop_table("analysis_runs")
    op.drop_index(op.f("ix_resumes_user_id"), table_name="resumes")
    op.drop_table("resumes")
    op.drop_index(op.f("ix_jobs_user_id"), table_name="jobs")
    op.drop_table("jobs")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
