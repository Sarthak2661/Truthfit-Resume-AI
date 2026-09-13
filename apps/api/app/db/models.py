from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import JSON


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return uuid4().hex


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    resumes: Mapped[list["Resume"]] = relationship(back_populates="user")
    jobs: Mapped[list["Job"]] = relationship(back_populates="user")
    analysis_runs: Mapped[list["AnalysisRun"]] = relationship(back_populates="user")


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    parsed_text: Mapped[str] = mapped_column(Text, nullable=False)
    redacted_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    user: Mapped[User] = relationship(back_populates="resumes")
    analysis_runs: Mapped[list["AnalysisRun"]] = relationship(back_populates="resume")


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    company: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    user: Mapped[User] = relationship(back_populates="jobs")
    analysis_runs: Mapped[list["AnalysisRun"]] = relationship(back_populates="job")


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    resume_id: Mapped[str] = mapped_column(ForeignKey("resumes.id"), index=True, nullable=False)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    model: Mapped[str] = mapped_column(String(120), nullable=False)
    overall_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    result_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="analysis_runs")
    resume: Mapped[Resume] = relationship(back_populates="analysis_runs")
    job: Mapped[Job] = relationship(back_populates="analysis_runs")
    evidence: Mapped[list["Evidence"]] = relationship(back_populates="analysis_run")
    agent_events: Mapped[list["AgentEvent"]] = relationship(back_populates="analysis_run")


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    analysis_run_id: Mapped[str] = mapped_column(ForeignKey("analysis_runs.id"), index=True, nullable=False)
    requirement: Mapped[str] = mapped_column(Text, nullable=False)
    resume_evidence: Mapped[str] = mapped_column(Text, default="", nullable=False)
    evidence_type: Mapped[str] = mapped_column(String(80), default="general", nullable=False)
    confidence: Mapped[str] = mapped_column(String(40), default="unknown", nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    analysis_run: Mapped[AnalysisRun] = relationship(back_populates="evidence")


class AgentEvent(Base):
    __tablename__ = "agent_events"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    analysis_run_id: Mapped[str] = mapped_column(ForeignKey("analysis_runs.id"), index=True, nullable=False)
    agent_name: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_type: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    analysis_run: Mapped[AnalysisRun] = relationship(back_populates="agent_events")
