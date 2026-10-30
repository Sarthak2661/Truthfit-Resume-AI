import Link from "next/link";
import { ErrorPanel } from "../../components/ErrorPanel";
import { getTrackedJobs } from "../../lib/api";

export default async function TrackerPage() {
  try {
    const tracker = await getTrackedJobs();
    const columns = ["Saved", "Applied", "Interview", "Rejected"];

    return (
      <section className="section">
        <div className="section-label">Job tracker</div>
        <h1>Tracked opportunities</h1>
        <p className="muted">Move from review to action with saved roles, match scores, application status, notes, and evidence links.</p>

        <div className="section kanban">
          {columns.map((column) => {
            const jobs = tracker.jobs.filter((job) => job.tracker_status === column);
            return (
              <section className="kanban-column" key={column}>
                <div className="kanban-head">
                  <h3>{column}</h3>
                  <span className={`status ${statusClass(column)}`}>{jobs.length}</span>
                </div>
                <div className="kanban-stack">
                  {jobs.map((job) => (
                    <article className="job-card" key={job.run_id}>
                      <div>
                        <span className="section-label">{job.company}</span>
                        <h3>{job.role}</h3>
                        <p className="muted">{job.location || "Location not specified"}</p>
                      </div>
                      <div className="job-card-meta">
                        <span className="pill">{job.match_score}/100 match</span>
                        <span className={`status ${statusClass(job.tracker_status)}`}>{job.tracker_status}</span>
                      </div>
                      {job.job_link ? (
                        <a className="settings-link" href={job.job_link} target="_blank" rel="noreferrer">
                          Open job post
                        </a>
                      ) : (
                        <span className="muted">No job link saved</span>
                      )}
                      <div>
                        <span className="section-label">Top fixes</span>
                        {job.top_fixes.length ? (
                          job.top_fixes.map((fix) => (
                            <p className="muted" key={fix}>
                              {fix}
                            </p>
                          ))
                        ) : (
                          <p className="muted">No fixes saved for this run.</p>
                        )}
                      </div>
                      <div>
                        <span className="section-label">Notes</span>
                        <p className="muted">{job.notes || "No notes yet."}</p>
                      </div>
                      <Link className="button secondary" href={job.analysis_url}>
                        Open analysis
                      </Link>
                    </article>
                  ))}
                  {!jobs.length ? <p className="muted">No {column.toLowerCase()} roles.</p> : null}
                </div>
              </section>
            );
          })}
        </div>
        {!tracker.jobs.length ? (
          <div className="section alert">No tracked jobs yet. Open an analysis and save the opportunity.</div>
        ) : null}
      </section>
    );
  } catch (error) {
    return <ErrorPanel message={error instanceof Error ? error.message : "Unknown API error"} />;
  }
}

function statusClass(value: string): string {
  const normalized = value.toLowerCase();
  if (normalized.includes("interview")) {
    return "good";
  }
  if (normalized.includes("rejected")) {
    return "bad";
  }
  return "warn";
}
