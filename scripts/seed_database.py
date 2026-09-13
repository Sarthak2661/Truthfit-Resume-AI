from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from apps.api.app.db.database import init_db, session_scope  # noqa: E402
from apps.api.app.db import repositories  # noqa: E402
from source.services.sample_analysis import sample_analysis_result  # noqa: E402
from source.services.resume_heatmap import redact_personal_details  # noqa: E402


def main() -> None:
    init_db()
    resume_text = "Demo Candidate\nPython, SQL, PostgreSQL, Kafka, Streamlit"
    job_text = "Data Engineer role requiring Python, SQL, PostgreSQL, pipelines, and dashboards."
    analysis = sample_analysis_result()

    with session_scope() as session:
        user = repositories.get_or_create_user(session, "demo@truthfit.local")
        resume = repositories.create_resume(
            session=session,
            user_id=user.id,
            file_name="sample_resume.txt",
            parsed_text=resume_text,
            redacted_text=redact_personal_details(resume_text),
        )
        job = repositories.create_job(
            session=session,
            user_id=user.id,
            title="Data Engineer",
            company="Northstar Analytics",
            description=job_text,
        )
        run = repositories.create_analysis_run(
            session=session,
            user_id=user.id,
            resume_id=resume.id,
            job_id=job.id,
            provider="Demo",
            model="sample-analysis",
        )
        repositories.complete_analysis_run(session, run, analysis)
        repositories.add_evidence_records(session, run.id, analysis)
        repositories.add_agent_event(session, run.id, "seed", "completed")
        print(f"Seeded demo analysis run: {run.id}")


if __name__ == "__main__":
    main()
